from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Set
import itertools
import logging
import re
from datetime import datetime
import pdfplumber

from ..utils.io import read_json, write_json
from ..utils.ocr import ocr_page, DEFAULT_OCR_DPI, DEFAULT_OCR_LANGS


EXTRACT_CACHE = "extracted.json"

# Regex to detect dates like 2023-01-30 or 01/30/2023
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})")


def extract_from_reports(reports_dir: Path, data_dir: Path, cache: bool = True, ocr: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    cache_path = data_dir / EXTRACT_CACHE
    if cache and cache_path.exists():
        cached = read_json(cache_path, default=[])
        if cached:
            return cached

    results: List[Dict[str, Any]] = []
    pdf_files = [p for p in reports_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"]
    for pdf_path in sorted(pdf_files):
        results.extend(extract_from_pdf(pdf_path, ocr=ocr))

    if cache:
        write_json(cache_path, results)
    return results


def extract_from_pdf(pdf_path: Path, ocr: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str, str]] = set()  # (file, name_lower, value_raw)
    try:
        fallback_date = datetime.fromtimestamp(pdf_path.stat().st_mtime).date().isoformat()
        with pdfplumber.open(pdf_path) as pdf:
            report_date: Optional[str] = None
            for pi, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if ocr and ocr.get("enabled"):
                    mode = str(ocr.get("mode", "auto")).lower()
                    need_ocr = mode == "always" or (mode == "auto" and not text)
                    if need_ocr:
                        dpi = int(ocr.get("dpi", DEFAULT_OCR_DPI))
                        langs = ocr.get("languages", DEFAULT_OCR_LANGS)
                        t_cmd = ocr.get("tesseract_cmd")
                        logging.debug(
                            "Attempting OCR for %s page %s (dpi=%s, langs=%s)",
                            pdf_path.name,
                            pi,
                            dpi,
                            langs,
                        )
                        text_ocr = ocr_page(
                            pdf_path,
                            pi,
                            dpi=dpi,
                            languages=langs,
                            tesseract_cmd=t_cmd,
                        )
                        if text_ocr:
                            text = f"{text}\n{text_ocr}".strip()
                if not report_date:
                    report_date = _find_first_date(text)

                # 1) Parse any table-like blocks by treating cells as text lines
                tables = page.extract_tables() or []
                for tbl in tables:
                    for raw_row in tbl:
                        for cell in raw_row:
                            line = (cell or "").strip()
                            if not line:
                                continue
                            for rec in _parse_result_lines([line], pdf_path, default_date=report_date or fallback_date):
                                key = (rec["file"], rec["test_name"].lower(), rec.get("value_raw", ""))
                                if key not in seen:
                                    rows.append(rec)
                                    seen.add(key)

                # 2) Also parse raw text lines to catch non-table content
                for rec in _parse_result_lines(
                    [ln.strip() for ln in text.splitlines() if ln.strip()],
                    pdf_path,
                    default_date=report_date or fallback_date,
                ):
                    key = (rec["file"], rec["test_name"].lower(), rec.get("value_raw", ""))
                    if key not in seen:
                        rows.append(rec)
                        seen.add(key)
    except Exception as e:
        rows.append({
            "file": str(pdf_path.name),
            "error": f"parse_error: {e}",
        })
    return rows


def _parse_result_lines(lines: List[str], pdf_path: Path, default_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse Quest-style result lines such as:
    - "GLUCOSE 81 Reference Range: 65-99 mg/dL"
    - "HEMOGLOBIN A1c 5.9 H Reference Range: <5.7 % of total Hgb"
    Returns a list of extracted measurement dicts.
    """
    out: List[Dict[str, Any]] = []

    # Pattern with Reference Range and optional unit near the end
    # Captures name, numeric value, optional H/L flag, range (a-b, <x, >x), and optional unit tokens
    pat_range = re.compile(
        r"^(?P<name>[A-Za-z0-9 ,.:()/%+\-]+?)\s+"  # allow commas/colons
        r"(?P<value>[-+]?\d+(?:\.\d+)?)\s*"
        r"(?P<flag>[HL])?\s*"
        r"(?:[A-Za-z%/().\-\s]*)?"  # optional tokens like units or (calc)
        r"Reference\s*Range:\s*"
        r"(?P<range>"
        r"<\s*(?:OR\s*=\s*)?[-+]?\d+(?:\.\d+)?|"
        r">\s*(?:OR\s*=\s*)?[-+]?\d+(?:\.\d+)?|"
        r"[-+]?\d+(?:\.\d+)?\s*-\s*[-+]?\d+(?:\.\d+)?"
        r")"
        r"(?:\s*(?P<unit>[A-Za-z%/]+(?:/[A-Za-z]+)?))?",
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Simpler pattern without explicit Reference Range (fallback)
    pat_simple = re.compile(
        r"^(?P<name>[A-Za-z0-9 .()/%+-]+?)\s+"
        r"(?P<value>[-+]?\d+(?:\.\d+)?)\s*"
        r"(?P<unit>[A-Za-z%/]+)?$"
    )

    for ln in lines:
        # Skip administrative/legal lines quickly
        if "Quest Diagnostics" in ln or "Privacy policy" in ln or ln.startswith("Phone:"):
            continue

        m = pat_range.match(ln)
        if m:
            name = m.group("name").strip()
            value_raw = m.group("value").strip()
            flag = (m.group("flag") or "").strip()
            rng = (m.group("range") or "").strip()
            unit_token = (m.group("unit") or "").strip()
            unit_guess = _unit_from_tokens(unit_token, ln)
            low, high = _parse_ref_range(rng)

            out.append({
                "file": pdf_path.name,
                "test_name": name,
                "value_raw": f"{value_raw}{(' ' + flag) if flag else ''}",
                "value_numeric": _extract_numeric(value_raw),
                "unit_raw": unit_guess or "",
                "ref_range_raw": f"{rng} {unit_token}".strip(),
                "measured_at": _find_first_date(ln) or default_date,
            })
            continue

        # Fallback simple numeric line (no explicit Reference Range)
        m2 = pat_simple.match(ln)
        if m2:
            name = m2.group("name").strip()
            value_raw = m2.group("value").strip()
            unit_token = (m2.group("unit") or "").strip()
            unit_guess = _unit_from_tokens(unit_token, ln)
            out.append({
                "file": pdf_path.name,
                "test_name": name,
                "value_raw": value_raw,
                "value_numeric": _extract_numeric(value_raw),
                "unit_raw": unit_guess or "",
                "ref_range_raw": "",
                "measured_at": _find_first_date(ln) or default_date,
            })
            continue

        # Qualitative urinalysis line: "COLOR YELLOW Reference Range: YELLOW" (case-insensitive)
        if re.search(r"Reference\s*Range:", ln, flags=re.IGNORECASE) and not re.search(r"\d", ln):
            parts = ln.split("Reference Range:")
            name = parts[0].strip()
            ref = parts[1].strip()
            out.append({
                "file": pdf_path.name,
                "test_name": name,
                "value_raw": "",
                "value_numeric": None,
                "unit_raw": "",
                "ref_range_raw": ref,
                "measured_at": _find_first_date(ln) or default_date,
            })

    return out


def _parse_ref_range(rng: str) -> Tuple[Optional[float], Optional[float]]:
    rng = rng.strip()
    # formats: "65-99" | "<5.7" | ">3.2"
    if not rng:
        return None, None
    if rng.startswith("<"):
        val = _extract_numeric(rng)
        return None, val
    if rng.startswith(">"):
        val = _extract_numeric(rng)
        return val, None
    if "-" in rng:
        try:
            a, b = [x.strip() for x in rng.split("-", 1)]
            return _extract_numeric(a), _extract_numeric(b)
        except Exception:
            return None, None
    return None, None


def _unit_from_tokens(unit_token: str, full_line: str) -> str:
    # If a unit token is captured, use it; else infer from line snippets
    if unit_token:
        tok = unit_token.strip()
        if re.fullmatch(r"(%|[A-Za-z]+/[A-Za-z]+|[A-Za-z]+/dL|[A-Za-z]+/uL|g/dL|mg/dL|mmol/L|U/L)", tok):
            return tok
    # If the line mentions a percent anywhere, prefer "%"
    if "%" in full_line:
        return "%"
    # Common count units may be embedded in text
    for u in ["mg/dL", "mmol/L", "Thousand/uL", "Million/uL", "U/L", "g/dL"]:
        if u in full_line:
            return u
    return ""


def _find_col(headers: list[str], candidates: list[str]) -> int | None:
    lower = [h.lower() for h in headers]
    for cand in candidates:
        if cand in lower:
            return lower.index(cand)
    return None


def _extract_unit_from_name(name: str) -> str | None:
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        token = m.group(1).strip()
        if _looks_like_unit(token):
            return token
    return None


def _extract_unit_from_value(value: str) -> str | None:
    m = re.search(r"([a-zA-Z%/]+)$", value)
    if m:
        token = m.group(1).strip()
        if _looks_like_unit(token):
            return token
    return None


def _looks_like_unit(token: str) -> bool:
    return bool(re.match(r"^[a-zA-Z%/0-9.]+$", token)) and len(token) <= 20


def _extract_numeric(s: str) -> float | None:
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    if m:
        try:
            return float(m.group(0))
        except Exception:
            return None
    return None


def _find_first_date(text: str) -> Optional[str]:
    """Return the first date found in ``text`` normalized to ISO format."""
    m = DATE_RE.search(text)
    if not m:
        return None
    return _parse_date_token(m.group(0))


def _parse_date_token(token: str) -> Optional[str]:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            dt = datetime.strptime(token, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue
    return None

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .catalog import load_catalog, build_synonym_map
from .units import canonicalize_unit, convert
from ..utils.io import write_json


NORMALIZED_CACHE = "normalized.json"


def normalize_measurements(extracted: List[Dict[str, Any]], data_dir: Path, units_preference: str = "auto") -> List[Dict[str, Any]]:
    catalog = load_catalog()
    synmap = build_synonym_map(catalog)
    tests = catalog.get("tests", {})

    normalized: List[Dict[str, Any]] = []
    for row in extracted:
        name = (row.get("test_name") or "").strip()
        if not name:
            continue
        code = synmap.get(name.lower())
        if not code:
            # Try simple cleanup (remove unit in name)
            cleaned = _strip_unit_from_name(name)
            code = synmap.get(cleaned.lower())
        if not code:
            code = name.upper().replace(" ", "_")[:20]

        tdef = tests.get(code, {})
        unit_raw = canonicalize_unit(row.get("unit_raw") or "")
        value = row.get("value_numeric")

        unit_final = unit_raw
        value_final = value

        # Determine canonical conversion
        canonical = tdef.get("unit_canonical")
        conversions = tdef.get("conversions", {})

        if units_preference == "canonical" and value is not None and canonical:
            if unit_raw and unit_raw != canonical:
                key = f"{unit_raw}->{canonical}"
                factor = conversions.get(key)
                if factor:
                    value_final, unit_final = convert(value, unit_raw, canonical, factor)
        elif units_preference == "auto" and value is not None and canonical:
            # If unit missing or suspicious, prefer canonical
            if (not unit_raw or len(unit_raw) > 12) and canonical:
                unit_final = canonical
            if unit_final != canonical and unit_final and canonical:
                key = f"{unit_final}->{canonical}"
                factor = conversions.get(key)
                if factor:
                    value_final, unit_final = convert(value, unit_final, canonical, factor)

        normalized.append({
            "file": row.get("file"),
            "test_code": code,
            "test_name": tdef.get("name", name),
            "category": tdef.get("category", "unknown"),
            "value": value_final,
            "unit": unit_final or canonical or "",
            "unit_raw": row.get("unit_raw"),
            "ref_low": (tdef.get("ref_range") or {}).get("low"),
            "ref_high": (tdef.get("ref_range") or {}).get("high"),
            "measured_at": row.get("measured_at"),
        })

    write_json(data_dir / NORMALIZED_CACHE, normalized)
    return normalized


def _strip_unit_from_name(name: str) -> str:
    # Remove trailing unit in parentheses
    if "(" in name and name.endswith(")"):
        base = name[: name.rfind("(")].strip()
        return base
    return name


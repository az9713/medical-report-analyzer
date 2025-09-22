from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Tuple


STATUS_EMOJI = {
    "high": "🔴",
    "low": "🟠",
    "in_range": "🟢",
    "unknown": "⚪",
}


def build_semi_annual_reviews(
    normalized: List[Dict[str, Any]], *, today: date | None = None
) -> List[Dict[str, Any]]:
    """Summarize measurements into June and December semiannual reviews.

    Args:
        normalized: Sequence of normalized measurement dicts.
        today: Optional date used when no measurements exist (primarily for tests).

    Returns:
        A list of review dictionaries ordered chronologically by period end.
    """

    today = today or date.today()
    parsed: List[Dict[str, Any]] = []
    for row in normalized:
        dt_str = row.get("measured_at")
        if not dt_str:
            continue
        try:
            dt = datetime.fromisoformat(dt_str).date()
        except ValueError:
            continue
        status = _classify_status(row.get("value"), row.get("ref_low"), row.get("ref_high"))
        parsed.append({**row, "_date": dt, "status": status})

    years: Iterable[int]
    if parsed:
        years = sorted({r["_date"].year for r in parsed})
    else:
        years = [today.year]

    reviews: List[Dict[str, Any]] = []
    for yr in years:
        for half in (1, 2):
            start, end = _period_bounds(yr, half)
            period_rows = [r for r in parsed if start <= r["_date"] <= end]
            review = _build_period_review(period_rows, yr, half, start, end)
            reviews.append(review)

    return reviews


def _period_bounds(year: int, half: int) -> Tuple[date, date]:
    if half == 1:
        return date(year, 1, 1), date(year, 6, 30)
    return date(year, 7, 1), date(year, 12, 31)


def _build_period_review(
    rows: List[Dict[str, Any]],
    year: int,
    half: int,
    start: date,
    end: date,
) -> Dict[str, Any]:
    label = "June" if half == 1 else "December"
    label = f"{label} {year} Semiannual Review"
    range_str = f"{start.strftime('%b %d, %Y')} – {end.strftime('%b %d, %Y')}"

    measurement_count = len(rows)
    unique_tests = len({r.get("test_code") for r in rows if r.get("test_code")})

    status_counts = Counter(r.get("status", "unknown") for r in rows)
    metrics = {
        "measurements": measurement_count,
        "unique_tests": unique_tests,
        "status": {
            "high": status_counts.get("high", 0),
            "low": status_counts.get("low", 0),
            "in_range": status_counts.get("in_range", 0),
            "unknown": status_counts.get("unknown", 0),
        },
    }

    if not rows:
        summary = (
            "No lab results were recorded between "
            f"{start.strftime('%b %d')} and {end.strftime('%b %d, %Y')}. "
            "Document the gap and plan the next screening window."
        )
        return {
            "label": label,
            "range": range_str,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": summary,
            "metrics": metrics,
            "highlights": [],
        }

    summary_parts = [
        (
            f"Collected {measurement_count} measurements across {unique_tests} tests "
            f"between {start.strftime('%b %d')} and {end.strftime('%b %d, %Y')}."
        )
    ]
    high_ct = metrics["status"]["high"]
    low_ct = metrics["status"]["low"]
    in_range_ct = metrics["status"]["in_range"]
    unknown_ct = metrics["status"]["unknown"]

    if high_ct or low_ct:
        summary_parts.append(
            f"Flagged {high_ct} high and {low_ct} low results, with {in_range_ct} measurements in range."
        )
    else:
        summary_parts.append(
            f"All scored measurements ({in_range_ct}) stayed within their reference ranges."
        )

    if unknown_ct:
        summary_parts.append(
            f"{unknown_ct} results lacked reference ranges and were noted for manual review."
        )

    if measurement_count < 3:
        summary_parts.append(
            "Limited data was available this period; interpret longitudinal trends cautiously."
        )

    highlights = _build_highlights(rows)

    return {
        "label": label,
        "range": range_str,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": " ".join(summary_parts),
        "metrics": metrics,
        "highlights": highlights,
    }


def _build_highlights(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    latest_by_code: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = row.get("test_code")
        if not code:
            continue
        existing = latest_by_code.get(code)
        if not existing or row["_date"] > existing["_date"]:
            latest_by_code[code] = row

    flagged = [r for r in latest_by_code.values() if r.get("status") in {"high", "low"}]
    flagged.sort(key=_deviation_amount, reverse=True)

    highlights = [_format_highlight(r) for r in flagged[:3]]
    if highlights:
        return highlights

    fallback = sorted(latest_by_code.values(), key=lambda r: r["_date"], reverse=True)
    out: List[Dict[str, Any]] = []
    for row in fallback[:3]:
        comment = (
            "Result stayed within the reference range."
            if row.get("status") == "in_range"
            else "Result recorded without a reference range."
        )
        out.append(_format_highlight(row, override_comment=comment))
    return out


def _format_highlight(row: Dict[str, Any], override_comment: str | None = None) -> Dict[str, Any]:
    comment = override_comment or _highlight_comment(row)
    unit = (row.get("unit") or "").strip()
    value_display = _format_value(row.get("value"))
    value_with_unit = f"{value_display} {unit}".strip()
    description = (
        f"{row.get('test_name', row.get('test_code', ''))} ({row['_date'].isoformat()}): "
        f"{value_with_unit or value_display}"
    )
    if comment:
        description = f"{description} — {comment}"

    status = row.get("status", "unknown")

    return {
        "test_code": row.get("test_code"),
        "status": status,
        "emoji": STATUS_EMOJI.get(status, "⚪"),
        "description": description,
    }


def _highlight_comment(row: Dict[str, Any]) -> str:
    status = row.get("status")
    value = row.get("value")
    low = row.get("ref_low")
    high = row.get("ref_high")

    if status == "high":
        if value is not None and high is not None:
            diff = value - high
            return (
                f"{_format_value(diff)} above the upper limit ({_format_value(high)})"
            )
        return "Result above the expected range."
    if status == "low":
        if value is not None and low is not None:
            diff = low - value
            return (
                f"{_format_value(diff)} below the lower limit ({_format_value(low)})"
            )
        return "Result below the expected range."
    if status == "in_range":
        return "Result stayed within the reference range."
    return "Reference range unavailable; monitor as new data arrives."


def _deviation_amount(row: Dict[str, Any]) -> float:
    value = row.get("value")
    if value is None:
        return 0.0
    status = row.get("status")
    if status == "high" and row.get("ref_high") is not None:
        return abs(value - row["ref_high"])
    if status == "low" and row.get("ref_low") is not None:
        return abs(row["ref_low"] - value)
    return 0.0


def _classify_status(value: Any, low: Any, high: Any) -> str:
    if value is None or (low is None and high is None):
        return "unknown"
    try:
        if low is not None and value < low:
            return "low"
        if high is not None and value > high:
            return "high"
    except TypeError:
        return "unknown"
    return "in_range"


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        return formatted or "0"
    return str(value)


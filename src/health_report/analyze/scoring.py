from __future__ import annotations

from typing import Any, Dict, List


def compute_scores(trended: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for r in trended:
        value = r.get("value")
        low = r.get("ref_low")
        high = r.get("ref_high")
        status = "unknown"
        if value is not None and (low is not None or high is not None):
            if low is not None and value < low:
                status = "low"
            elif high is not None and value > high:
                status = "high"
            else:
                status = "in_range"
        risk = 0
        if status == "high":
            risk = 2
        elif status == "low":
            risk = 1
        elif status == "in_range":
            risk = 0
        emoji = _status_emoji(status)
        scored.append({**r, "status": status, "risk": risk, "emoji": emoji})
    return scored


def _status_emoji(status: str) -> str:
    return {
        "in_range": "🟢",
        "low": "🟠",
        "high": "🔴",
    }.get(status, "⚪")


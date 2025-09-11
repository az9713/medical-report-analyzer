from __future__ import annotations

from typing import Any, Dict, List
import math


def compute_trends(normalized: List[Dict[str, Any]], rolling_window_days: int = 120) -> List[Dict[str, Any]]:
    # Placeholder: attach simple trend direction based on last 3 values order per test_code
    by_code: Dict[str, List[Dict[str, Any]]] = {}
    for row in normalized:
        if row.get("value") is None:
            continue
        by_code.setdefault(row["test_code"], []).append(row)

    trends: List[Dict[str, Any]] = []
    for code, rows in by_code.items():
        vals = [r["value"] for r in rows if r.get("value") is not None]
        direction = "stable"
        if len(vals) >= 3:
            if vals[-1] > vals[-2] > vals[-3]:
                direction = "up"
            elif vals[-1] < vals[-2] < vals[-3]:
                direction = "down"
        volatility = _std(vals[-5:]) if len(vals) >= 2 else 0.0
        for r in rows:
            trends.append({**r, "trend": direction, "volatility": volatility})
    return trends


def _std(vals: List[float]) -> float:
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


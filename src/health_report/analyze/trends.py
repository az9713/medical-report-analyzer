from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timedelta
import math


def compute_trends(
    normalized: List[Dict[str, Any]],
    rolling_window_days: int = 120,
    trend_min_points: int = 3,
    volatility_window: int = 5,
) -> List[Dict[str, Any]]:
    """Compute time-aware trends for normalized measurements.

    Measurements are grouped by ``test_code`` and sorted by ``measured_at``. Only
    values within ``rolling_window_days`` from the latest measurement are
    considered. A simple linear regression on day offsets vs. values provides the
    slope used to determine trend direction.
    """

    by_code: Dict[str, List[Dict[str, Any]]] = {}
    for row in normalized:
        if row.get("value") is None or not row.get("measured_at"):
            continue
        by_code.setdefault(row["test_code"], []).append(row)

    trends: List[Dict[str, Any]] = []
    for code, rows in by_code.items():
        # Sort by measurement date
        rows_sorted = sorted(rows, key=lambda r: r["measured_at"])  # ISO date str
        latest_dt = datetime.fromisoformat(rows_sorted[-1]["measured_at"])
        window_start = latest_dt - timedelta(days=rolling_window_days)
        windowed = [
            r
            for r in rows_sorted
            if datetime.fromisoformat(r["measured_at"]) >= window_start
        ]

        if len(windowed) < trend_min_points:
            direction = "stable"
            slope = 0.0
        else:
            xs = [datetime.fromisoformat(r["measured_at"]).toordinal() for r in windowed]
            ys = [r["value"] for r in windowed]
            n = len(xs)
            sum_x = sum(xs)
            sum_y = sum(ys)
            sum_xx = sum(x * x for x in xs)
            sum_xy = sum(x * y for x, y in zip(xs, ys))
            denom = n * sum_xx - sum_x ** 2
            slope = (n * sum_xy - sum_x * sum_y) / denom if denom else 0.0
            if slope > 0:
                direction = "up"
            elif slope < 0:
                direction = "down"
            else:
                direction = "stable"

        last_vals = [r["value"] for r in windowed[-volatility_window:]]
        volatility = _std(last_vals) if len(last_vals) >= 2 else 0.0

        for r in windowed:
            trends.append({**r, "trend": direction, "volatility": volatility, "slope": slope})

    return trends


def _std(vals: List[float]) -> float:
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))

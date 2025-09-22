from health_report.analyze.trends import compute_trends


def _extract(code: str, values: list[float], start: str) -> list[dict]:
    from datetime import datetime, timedelta
    start_dt = datetime.fromisoformat(start)
    rows = []
    for i, val in enumerate(values):
        rows.append({
            "test_code": code,
            "value": val,
            "measured_at": (start_dt + timedelta(days=i)).date().isoformat(),
        })
    return rows


def test_compute_trends_upward():
    data = _extract("A", [1, 2, 3], "2023-01-01")
    out = compute_trends(data, rolling_window_days=30, trend_min_points=2)
    latest = out[-1]
    assert latest["trend"] == "up"
    assert latest["slope"] > 0


def test_compute_trends_downward():
    data = _extract("B", [3, 2, 1], "2023-01-01")
    out = compute_trends(data, rolling_window_days=30, trend_min_points=2)
    latest = out[-1]
    assert latest["trend"] == "down"
    assert latest["slope"] < 0


def test_compute_trends_insufficient_points():
    data = _extract("C", [1, 2, 3], "2023-01-01")
    out = compute_trends(data, rolling_window_days=30, trend_min_points=5)
    assert out[-1]["trend"] == "stable"
    assert out[-1]["slope"] == 0

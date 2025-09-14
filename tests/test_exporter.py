import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.health_report.exporter import export_data


def test_export_csv_and_json(tmp_path: Path):
    data = [
        {
            "test_code": "GLU",
            "test_name": "Glucose",
            "value": 90,
            "unit": "mg/dL",
            "measured_at": "2024-01-01",
            "trend": "stable",
            "slope": 0,
            "volatility": 0,
            "status": "in_range",
            "risk": 0,
            "emoji": "🟢",
        }
    ]
    export_data(data, tmp_path, ["csv", "json"])

    csv_path = tmp_path / "results.csv"
    json_path = tmp_path / "results.json"
    assert csv_path.exists()
    assert json_path.exists()

    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["test_code"] == "GLU"

    loaded = json.loads(json_path.read_text())
    assert loaded[0]["test_code"] == "GLU"

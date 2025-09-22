from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List
import csv

from .utils.io import write_json


def export_data(data: List[Dict[str, Any]], out_dir: Path, formats: Iterable[str]) -> None:
    """Export analysis results to ``out_dir`` in the given formats.

    Supported formats: ``json`` and ``csv``.
    ``data`` is a list of dictionaries representing measurements with
    trend and scoring information.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt_set = {f.lower() for f in formats}

    if "json" in fmt_set:
        write_json(out_dir / "results.json", data)

    if "csv" in fmt_set and data:
        fieldnames = sorted({k for row in data for k in row.keys()})
        with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

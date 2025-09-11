from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json


def load_catalog(path: Path | None = None) -> Dict[str, Any]:
    if path is None:
        path = Path("data/metrics_catalog.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_synonym_map(catalog: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for code, info in catalog.get("tests", {}).items():
        mapping[code.lower()] = code
        for syn in info.get("synonyms", []):
            mapping[syn.lower()] = code
    return mapping


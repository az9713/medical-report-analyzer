from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def ensure_dirs(paths: list[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any | None = None) -> Any:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


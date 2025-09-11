from __future__ import annotations

from typing import Tuple, Optional


def canonicalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    u = unit.strip().replace(" ", "")
    aliases = {
        "mgdl": "mg/dL",
        "mmoll": "mmol/L",
        "uiuml": "uIU/mL",
        "miul": "mIU/L",
        "ul": "U/L",
    }
    key = u.lower()
    return aliases.get(key, unit)


def convert(value: float, from_unit: str, to_unit: str, factor: Optional[float]) -> Tuple[float, str]:
    if from_unit == to_unit or factor is None:
        return value, from_unit
    return value * factor, to_unit


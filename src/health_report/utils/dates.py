from __future__ import annotations

from datetime import datetime
from dateutil import parser


def parse_date(s: str) -> datetime | None:
    try:
        return parser.parse(s, fuzzy=True)
    except Exception:
        return None


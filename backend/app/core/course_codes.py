"""Course codes written one way everywhere, so agents, searches and database keys agree."""

from __future__ import annotations

import re

_COURSE_CODE = re.compile(r"^([A-Z]+)\s*(\d{3}[A-Z]?)$")


def normalize_course_code(value: str) -> str:
    """Turn "cmput301" or "CMPUT  301" into "CMPUT 301". Unrecognized codes are only upper-cased."""
    compact = " ".join(value.upper().split())
    match = _COURSE_CODE.match(compact)
    return f"{match[1]} {match[2]}" if match else compact

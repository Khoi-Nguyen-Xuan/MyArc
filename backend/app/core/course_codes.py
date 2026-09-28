"""Course codes and titles written one way everywhere, so agents, searches,
database keys and the dashboard agree."""

from __future__ import annotations

import re

# subject letters + 3-digit number, with an optional one-letter suffix
# ("CMPUT 174B"). The suffix is only taken when nothing follows it, so a
# section tag like "A1" in "CMPUT201A1" is not mistaken for part of the code.
_COURSE_CODE = re.compile(r"([A-Z]{2,})\s*(\d{3})(?!\d)(?:([A-Z])(?![A-Z0-9]))?")

_SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"}
_ROMAN = re.compile(r"^(?=[IVX]+$)X{0,3}(IX|IV|V?I{0,3})$")


def normalize_course_code(value: str) -> str:
    """Turn "cmput301", "CMPUT  301" or "CMPUT201A1 (51557)" into "CMPUT 301"/"CMPUT 201".
    Strings with no recognizable code are only upper-cased."""
    compact = " ".join(value.upper().split())
    match = _COURSE_CODE.search(compact)
    if not match:
        return compact
    subject, number, suffix = match.groups()
    return f"{subject} {number}{suffix or ''}"


def is_course_code(value: str) -> bool:
    """True for something a student could type as a course code: "CMPUT 201", "cmput201", "MATH 125A"."""
    return re.fullmatch(r"[A-Z]{2,}\s*\d{3}[A-Z]?", " ".join(value.upper().split())) is not None


def normalize_course_title(value: str) -> str:
    """Title-case a course name written in ALL CAPS or all lowercase:
    "PRACTICAL PROG METHODOLOGY" -> "Practical Prog Methodology".
    Titles that already mix cases ("Bioinformatics I") are kept as written."""
    title = " ".join(value.split())
    if not title or (title != title.upper() and title != title.lower()):
        return title

    words = title.split(" ")
    return " ".join(_title_word(word, first=(i == 0)) for i, word in enumerate(words))


def _title_word(word: str, *, first: bool) -> str:
    if _ROMAN.match(word.upper()):
        return word.upper()  # "Calculus I", "Physics II"
    if any(ch.isdigit() for ch in word):
        return word.upper()  # "3D", "C++11"
    if not first and word.lower() in _SMALL_WORDS:
        return word.lower()
    return "-".join(part[:1].upper() + part[1:].lower() for part in word.split("-"))

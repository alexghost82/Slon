"""Wake-word matching for Slon (no network, no audio I/O)."""

from __future__ import annotations

import re
import unicodedata

# Primary product wake word plus common ASR / locale variants.
WAKE_WORD = "Slon"
_WAKE_PATTERN = re.compile(
    r"(?<![a-zа-яё])(slon|sloon|слон)(?![a-zа-яё])",
    re.IGNORECASE,
)


def normalize_transcript(text: str) -> str:
    """Lowercase and fold accents for robust keyword checks."""
    folded = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return stripped.lower().replace("ё", "е")


def contains_wake_word(text: str) -> bool:
    """Return True if ``text`` contains the Slon wake word (EN/RU ASR forms)."""
    return _WAKE_PATTERN.search(normalize_transcript(text)) is not None


__all__ = [
    "WAKE_WORD",
    "contains_wake_word",
    "normalize_transcript",
]

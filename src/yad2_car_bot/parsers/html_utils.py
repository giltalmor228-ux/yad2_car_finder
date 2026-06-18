from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup, Tag
from typing import Optional


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def safe_text(tag: Optional[Tag]) -> Optional[str]:
    """Return stripped text from a BS4 tag, or None if tag is None."""
    if tag is None:
        return None
    text = tag.get_text(separator=" ", strip=True)
    return text if text else None


# Hebrew punctuation and special chars to strip during normalization
_STRIP_PATTERN = re.compile(r"[׳״\u05F3\u05F4\u200b\u200f\-_.,;:!?\"'()\[\]{}]")


def normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for keyword matching.

    - Strip punctuation (including Hebrew geresh ׳ and gershayim ״)
    - Collapse whitespace
    - Preserve phrase structure (lower-cased for comparison)
    """
    text = unicodedata.normalize("NFC", text)
    text = _STRIP_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

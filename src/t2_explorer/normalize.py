"""Text cleaning, slugs, and API-row → TechRecord conversion."""

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SLUG_BAD_RE = re.compile(r"[^A-Za-z0-9._-]+")


def clean_text(value: str | None) -> str:
    """Strip embedded markup (e.g. search-highlight spans), decode entities, tidy spaces."""
    text = html.unescape(value or "")
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)  # entities may decode into text containing entities
    return _WS_RE.sub(" ", text).strip()


def slugify(case_number: str, record_id: str) -> str:
    """Filesystem/URL-safe slug from the case number, falling back to the record id."""
    base = _SLUG_BAD_RE.sub("-", case_number).strip("-")
    return base or record_id

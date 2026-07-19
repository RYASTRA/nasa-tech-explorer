"""Text cleaning, slugs, and API-row → TechRecord conversion."""

import html
import re

from .config import COLUMN_MAP
from .models import TechRecord

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SLUG_BAD_RE = re.compile(r"[^A-Za-z0-9._-]+")
_HL_SPAN_RE = re.compile(r"</?span[^>]*>")


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


def neutralize_raw(row: list) -> list:
    """Copy of the row with query-dependent artifacts removed (highlight spans, score).

    The API decorates matched terms with <span class="highlight"> and appends a
    relevance score in column 12; both vary with whichever harvest query first
    found the record, so storing them verbatim would churn nightly git diffs.
    """
    out = [_HL_SPAN_RE.sub("", col) if isinstance(col, str) else col for col in row]
    if len(out) == 13 and isinstance(out[12], (int, float)):
        out[12] = 0
    return out


def row_to_record(dataset: str, row: list, today: str) -> TechRecord:
    """Map one raw API row onto a TechRecord; raises ValueError if the row is unusable."""
    cols = COLUMN_MAP[dataset]

    def raw_col(name: str) -> str:
        idx = cols.get(name)
        if idx is None or idx >= len(row) or not isinstance(row[idx], str):
            return ""
        return row[idx]

    record_id = raw_col("id").strip()
    if not record_id:
        raise ValueError(f"{dataset} row has no id: {row[:2]!r}")
    case_number = clean_text(raw_col("case_number"))
    url = raw_col("url").strip()
    return TechRecord(
        dataset=dataset,
        id=record_id,
        case_number=case_number,
        title=clean_text(raw_col("title")),
        abstract=clean_text(raw_col("abstract")),
        category=clean_text(raw_col("category")).lower(),
        center=clean_text(raw_col("center")).upper(),
        url=url if url.startswith("http") else "",
        slug=slugify(case_number, record_id),
        raw=neutralize_raw(row),
        first_seen=today,
        last_seen=today,
    )

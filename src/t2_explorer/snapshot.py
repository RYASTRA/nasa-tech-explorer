"""Harvest, merge, staleness bookkeeping, guards, and data/ output."""

from .api import QueryError
from .config import (
    MAX_FAILED_QUERY_RATIO,
    MAX_SKIPPED_ROW_RATIO,
    MIN_KEEP_RATIO,
    MISS_LIMIT,
)
from .models import TechRecord
from .normalize import row_to_record


class SnapshotAborted(RuntimeError):
    """The snapshot must not be committed; the previous data/ stays authoritative."""


def harvest(dataset: str, client, terms: list[str]) -> tuple[dict[str, list], int]:
    """Union all keyword queries for one dataset, deduped by record id."""
    rows: dict[str, list] = {}
    failed = 0
    for term in terms:
        try:
            for row in client.fetch(dataset, term):
                if row and isinstance(row[0], str) and row[0]:
                    rows.setdefault(row[0], row)
        except QueryError:
            failed += 1
    return rows, failed


def check_failed_ratio(failed: int, total_queries: int) -> None:
    """Abort when too many queries failed — a partial harvest must not ratchet miss counts."""
    if total_queries and failed / total_queries > MAX_FAILED_QUERY_RATIO:
        raise SnapshotAborted(
            f"{failed}/{total_queries} queries failed (> {MAX_FAILED_QUERY_RATIO:.0%}); "
            "aborting so a flaky night cannot ratchet miss counts"
        )


def check_shrink(dataset: str, previous_count: int, new_count: int, force: bool) -> None:
    """Abort when tonight's harvest saw far fewer live records than the previous snapshot."""
    if force or not previous_count:
        return
    if new_count < previous_count * MIN_KEEP_RATIO:
        raise SnapshotAborted(
            f"{dataset} shrank {previous_count} -> {new_count} "
            f"(< {MIN_KEEP_RATIO:.0%}); set FORCE_SNAPSHOT=1 to accept"
        )


def merge(
    dataset: str,
    previous: dict[str, TechRecord],
    harvested: dict[str, list],
    today: str,
) -> tuple[dict[str, TechRecord], dict]:
    """Fold a harvest into the prior snapshot with first/last-seen and miss bookkeeping."""
    stats = {"new": 0, "updated": 0, "missed": 0, "dropped": 0, "skipped_rows": 0}
    merged: dict[str, TechRecord] = {}
    for record_id, row in harvested.items():
        try:
            fresh = row_to_record(dataset, row, today)
        except ValueError:
            stats["skipped_rows"] += 1
            continue
        prior = previous.get(record_id)
        if prior:
            fresh.first_seen = prior.first_seen
            stats["updated"] += 1
        else:
            stats["new"] += 1
        merged[record_id] = fresh
    for record_id, prior in previous.items():
        if record_id in merged:
            continue
        prior.miss_count += 1
        if prior.miss_count >= MISS_LIMIT:
            stats["dropped"] += 1
            continue
        stats["missed"] += 1
        merged[record_id] = prior
    if harvested and stats["skipped_rows"] / len(harvested) > MAX_SKIPPED_ROW_RATIO:
        raise SnapshotAborted(
            f"{dataset}: {stats['skipped_rows']}/{len(harvested)} rows failed to normalize; "
            "column map has likely drifted"
        )
    return merged, stats

"""Harvest, merge, staleness bookkeeping, guards, and data/ output."""

import datetime as _dt
import json
import os
from collections import Counter
from pathlib import Path

from .api import QueryError, T2Client
from .config import (
    DATA_DIR,
    DATASETS,
    MAX_FAILED_QUERY_RATIO,
    MAX_SKIPPED_ROW_RATIO,
    MIN_KEEP_RATIO,
    MISS_LIMIT,
    QUERY_TERMS,
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


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def load_records(dataset: str, data_dir: Path) -> dict[str, TechRecord]:
    """Read one dataset's committed snapshot; empty dict when none exists yet."""
    path = data_dir / f"{dataset}.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = [TechRecord.from_dict(d) for d in payload["records"]]
    return {record.id: record for record in records}


def _facet_counts(records: dict[str, TechRecord]) -> dict:
    categories = Counter(r.category for r in records.values() if r.category)
    centers = Counter(r.center for r in records.values() if r.center)
    return {"category": dict(categories), "center": dict(centers)}


def run_snapshot(client=None, terms=None, today=None, force=None, data_dir=None) -> dict:
    """Harvest every dataset, merge, guard, and write data/*.json. Returns the meta dict."""
    client = client or T2Client()
    terms = list(terms if terms is not None else QUERY_TERMS)
    today = today or _dt.date.today().isoformat()
    force = force if force is not None else os.environ.get("FORCE_SNAPSHOT") == "1"
    data_dir = data_dir or DATA_DIR

    merged_by_dataset: dict[str, dict[str, TechRecord]] = {}
    meta_datasets: dict[str, dict] = {}
    for dataset in DATASETS:
        previous = load_records(dataset, data_dir)
        harvested, failed = harvest(dataset, client, terms)
        check_failed_ratio(failed, len(terms))
        merged, stats = merge(dataset, previous, harvested, today)
        check_shrink(dataset, len(previous), stats["new"] + stats["updated"], force)
        merged_by_dataset[dataset] = merged
        meta_datasets[dataset] = {
            "total": len(merged),
            "failed_queries": failed,
            "queries": len(terms),
            **stats,
        }

    # all guards passed for all datasets -> now (and only now) write
    for dataset, merged in merged_by_dataset.items():
        records = sorted(merged.values(), key=lambda r: (r.slug, r.id))
        _write_json(data_dir / f"{dataset}.json", {"records": [r.to_dict() for r in records]})
    _write_json(
        data_dir / "facets.json",
        {dataset: _facet_counts(merged) for dataset, merged in merged_by_dataset.items()},
    )
    meta = {
        "fetched_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "datasets": meta_datasets,
    }
    _write_json(data_dir / "meta.json", meta)
    return meta

"""Tests for the Observatory status.json contract (schema 1)."""

import json

from t2_explorer.models import TechRecord
from t2_explorer.site import build_site, build_status
from t2_explorer.snapshot import run_snapshot


def _software(case_number: str, first_seen: str, title: str = "Tool") -> TechRecord:
    return TechRecord(
        dataset="software",
        id="a" * 24,
        case_number=case_number,
        title=title,
        abstract="x",
        category="data processing",
        center="GRC",
        url="",
        slug=case_number,
        raw=[],
        first_seen=first_seen,
        last_seen=first_seen,
        miss_count=0,
    )


def _meta(*, failed: int = 0) -> dict:
    counts = {"total": 10, "new": 2, "failed_queries": failed}
    return {
        "fetched_at": "2026-07-21T07:50:09+00:00",
        "datasets": {name: dict(counts) for name in ("patent", "patent_issued", "software", "spinoff")},
    }


def test_build_status_envelope_ordering_and_normalized_timestamp():
    records = [
        _software("SW-OLD", "2026-07-01"),
        _software("SW-NEWEST", "2026-07-15"),
        _software("SW-MID", "2026-07-10"),
        TechRecord(  # patents never appear in the "newest software" items
            dataset="patent", id="b" * 24, case_number="PAT-1", title="P", abstract="x",
            category="c", center="GRC", url="", slug="PAT-1", raw=[],
            first_seen="2026-07-20", last_seen="2026-07-20", miss_count=0,
        ),
    ]
    doc = build_status(_meta(), records)

    assert doc["schema"] == 1
    assert doc["project"] == "nasa-tech-explorer"
    assert doc["site"] == "https://ryastra.github.io/nasa-tech-explorer/"
    assert doc["fresh_for_hours"] == 36
    assert doc["ok"] is True
    assert doc["updated_utc"] == "2026-07-21T07:50:09Z"  # +00:00 normalized to Z
    assert doc["headline"] == "40 records mirrored — 10 software packages"

    metrics = {m["label"]: m["value"] for m in doc["metrics"]}
    assert metrics["New last snapshot"] == "8"
    assert 1 <= len(doc["metrics"]) <= 4

    assert [i["text"].split(" (")[0] for i in doc["items"]] == ["Tool", "Tool", "Tool"]
    assert [i["when_utc"] for i in doc["items"]] == ["2026-07-15", "2026-07-10", "2026-07-01"]
    assert doc["items"][0]["url"] == "https://software.nasa.gov/search?q=SW-NEWEST"
    assert all(len(i["text"]) <= 140 for i in doc["items"])
    assert len(doc["headline"]) <= 120


def test_failed_queries_flip_ok():
    assert build_status(_meta(failed=1), [])["ok"] is False


def test_build_site_writes_status_json(tmp_path):
    class OneSoftware:
        def fetch(self, dataset, term):
            if dataset != "software":
                return []
            return [["c" * 24, "MSC-1", "Nav Tool", "abstract", "", "cat", "", "", "", "JSC", "", "", 1.0]]

    data_dir, site_dir = tmp_path / "data", tmp_path / "site"
    run_snapshot(client=OneSoftware(), terms=["x"], today="2026-07-19", force=False, data_dir=data_dir)
    build_site(data_dir=data_dir, site_dir=site_dir)

    doc = json.loads((site_dir / "status.json").read_text(encoding="utf-8"))
    assert doc["project"] == "nasa-tech-explorer"
    assert doc["items"][0]["text"].startswith("Nav Tool")

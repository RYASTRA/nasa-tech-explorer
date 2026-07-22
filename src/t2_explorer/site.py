"""Render the static site from data/ into site/."""

import gzip
import json
import shutil
import urllib.parse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import (
    ASSETS_DIR,
    DATA_DIR,
    DATASET_LABELS,
    DATASETS,
    INDEX_ABSTRACT_CHARS,
    INDEX_GZIP_BUDGET,
    LINK_LABELS,
    SITE_BASE_URL,
    SITE_DIR,
    TEMPLATES_DIR,
    URL_SEGMENT,
)
from .models import TechRecord
from .snapshot import load_records


class BuildError(RuntimeError):
    """The site could not be built within its constraints."""


def official_link(record: TechRecord) -> str:
    """Deep link to the official NASA page for this record (URL patterns verified live)."""
    if record.dataset in ("patent", "patent_issued") and record.case_number:
        return f"https://technology.nasa.gov/patent/{urllib.parse.quote(record.case_number)}"
    if record.dataset == "software":
        query = urllib.parse.quote(record.case_number or record.title)
        return f"https://software.nasa.gov/search?q={query}"
    if record.dataset == "spinoff" and record.url:
        return record.url
    return "https://spinoff.nasa.gov/"


def _resolve_slugs(records: list[TechRecord]) -> list[tuple[TechRecord, str]]:
    """Give every record a unique per-dataset slug (two entries can share a case number)."""
    taken: set[tuple[str, str]] = set()
    resolved = []
    for record in records:
        slug = record.slug
        if (record.dataset, slug) in taken:
            slug = f"{record.slug}--{record.id[:8]}"
        taken.add((record.dataset, slug))
        resolved.append((record, slug))
    return resolved


def _write_search_index(resolved: list[tuple[TechRecord, str]], site_dir: Path) -> None:
    for abstract_chars in (INDEX_ABSTRACT_CHARS, 200, 120):
        rows = [
            [
                r.dataset,
                slug,
                r.case_number,
                r.title,
                r.category,
                r.center,
                r.abstract[:abstract_chars],
            ]
            for r, slug in resolved
        ]
        raw = json.dumps({"rows": rows}, ensure_ascii=False).encode("utf-8")
        if len(gzip.compress(raw)) <= INDEX_GZIP_BUDGET:
            out = site_dir / "data" / "index.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
            return
    raise BuildError("search index exceeds gzip budget even at 120-char abstracts")


def build_site(data_dir=None, site_dir=None, assets_dir=None, templates_dir=None) -> None:
    """Render index, detail pages, sitemap, robots, assets, and the search index."""
    data_dir = data_dir or DATA_DIR
    site_dir = site_dir or SITE_DIR
    assets_dir = assets_dir or ASSETS_DIR
    templates_dir = templates_dir or TEMPLATES_DIR

    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    meta = json.loads((data_dir / "meta.json").read_text(encoding="utf-8"))

    all_records: list[TechRecord] = []
    for dataset in DATASETS:
        all_records.extend(load_records(dataset, data_dir).values())
    all_records.sort(key=lambda r: (r.dataset, r.slug, r.id))
    resolved = _resolve_slugs(all_records)

    detail_template = env.get_template("detail.html.j2")
    pages: list[str] = []
    for record, slug in resolved:
        rel = f"{URL_SEGMENT[record.dataset]}/{slug}.html"
        out = site_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            detail_template.render(
                record=record,
                dataset_label=DATASET_LABELS[record.dataset],
                link=official_link(record),
                link_label=LINK_LABELS[record.dataset],
            ),
            encoding="utf-8",
        )
        pages.append(rel)

    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "index.html").write_text(
        env.get_template("index.html.j2").render(
            fetched_at=meta["fetched_at"],
            total_records=len(all_records),
        ),
        encoding="utf-8",
    )
    (site_dir / "sitemap.xml").write_text(
        env.get_template("sitemap.xml.j2").render(base_url=SITE_BASE_URL, pages=pages),
        encoding="utf-8",
    )
    (site_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    if assets_dir.is_dir():
        shutil.copytree(assets_dir, site_dir / "assets", dirs_exist_ok=True)
    _write_search_index(resolved, site_dir)
    (site_dir / "status.json").write_text(
        json.dumps(build_status(meta, all_records), indent=1) + "\n", encoding="utf-8"
    )


def build_status(meta: dict, records: list[TechRecord]) -> dict:
    """The Observatory status contract (schema 1) for this site.

    Small, stable, display-ready — the NASA Observatory renders these strings
    verbatim (headline <= 120 chars, <= 5 items, item text <= 140 chars). The
    contract is specified in the nasa-observatory repo:
    docs/superpowers/specs/2026-07-22-nasa-observatory-design.md
    updated_utc is the SNAPSHOT's timestamp, not build time: a push-triggered
    redeploy rebuilds this file without refreshing data and must not look fresh.
    """
    datasets = meta["datasets"]
    total = sum(d["total"] for d in datasets.values())
    software_total = datasets["software"]["total"]
    newest_software = sorted(
        (r for r in records if r.dataset == "software"),
        key=lambda r: (r.first_seen, r.case_number),
        reverse=True,
    )[:5]
    return {
        "schema": 1,
        "project": "nasa-tech-explorer",
        "title": "T2 Tech-Transfer Explorer",
        "site": "https://ryastra.github.io/nasa-tech-explorer/",
        "updated_utc": meta["fetched_at"].replace("+00:00", "Z"),
        "fresh_for_hours": 36,
        "ok": all(d["failed_queries"] == 0 for d in datasets.values()),
        "headline": f"{total:,} records mirrored — {software_total:,} software packages"[:120],
        "metrics": [
            {"label": "Software", "value": f"{software_total:,}"},
            {
                "label": "Patents",
                "value": f"{datasets['patent']['total'] + datasets['patent_issued']['total']:,}",
            },
            {"label": "Spinoffs", "value": f"{datasets['spinoff']['total']:,}"},
            {
                "label": "New last snapshot",
                "value": f"{sum(d['new'] for d in datasets.values()):,}",
            },
        ],
        "items": [
            {
                "when_utc": r.first_seen,
                "text": _clip(f"{r.title} ({r.case_number}) — {r.center}"),
                "url": official_link(r),
            }
            for r in newest_software
        ],
    }


def _clip(text: str, limit: int = 140) -> str:
    """Truncate to the contract's item bound with an ellipsis, never mid-slice."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

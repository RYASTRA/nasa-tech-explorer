# 🧰 nasa-tech-explorer — NASA's tech, actually searchable

Discover what NASA will **license or give away**: patents available for licensing,
the free software catalog, and spinoff stories — in one fast, static explorer.

Pattern: **mirror + static explorer**. A nightly GitHub Actions job snapshots the
full Tech Transfer catalog into committed JSON; GitHub Pages serves a client-side
search UI over it. No servers, no backend, no API keys in the browser — the data
plane is Actions, the serving is Pages, the lineage is git history.

> **Status: 🚧 pre-development (design phase) — founded 2026-07-13.**

## The unmet need

NASA's Technology Transfer program exists to get this technology *used* — its
success is measured in licenses and adoption. But discovery on the official
surfaces is clunky, and most developers have no idea
[software.nasa.gov](https://software.nasa.gov) is full of code they can request
or download. A humane discovery layer directly serves both the public and the
T2 office's own mission.

## What it will do

1. **Nightly snapshot** — an Actions job pulls the full T2 catalog (patents /
   software / spinoffs) through the TechTransfer API into committed JSON
   (`NASA_API_KEY` lives only in an Actions secret).
2. **Static explorer** — GitHub Pages site with client-side fuzzy search,
   category and NASA-center filters, and plain-English detail pages deep-linking
   to [technology.nasa.gov](https://technology.nasa.gov) and
   [software.nasa.gov](https://software.nasa.gov).
3. **Later hook** — the nightly snapshot diff *is* a watcher feed:
   "new NASA software this week" as GitHub Issues / a digest, same repo, same
   audience.

## Audiences

- **Founders & engineers** hunting licensable NASA IP
- **Developers** who'd use NASA code today if they could find it
- **The curious** — spinoff stories of NASA tech in everyday life

## Data source

NASA **TechTransfer API** (`patent`, `patent_issued`, `software`, `spinoff`) via
`api.nasa.gov`. Requires `NASA_API_KEY` ([free](https://api.nasa.gov/)), supplied
as an Actions secret — never shipped to the browser.

## The RYASTRA fleet

| Repo | What it is |
|---|---|
| [nasa-defense](https://github.com/RYASTRA/nasa-defense) | Planetary-defense watch (the original watcher engine) |
| [nasa-space-weather](https://github.com/RYASTRA/nasa-space-weather) | Space-weather watch |
| **nasa-tech-explorer** | NASA patents, free software & spinoffs — searchable *(this repo)* |
| [nasa-space-biology](https://github.com/RYASTRA/nasa-space-biology) | Faceted explorer for OSDR space-biology studies |
| [nasa-mcp](https://github.com/RYASTRA/nasa-mcp) | All 16 NASA public APIs as an MCP server (R&D layer) |

## License

[MIT](LICENSE)

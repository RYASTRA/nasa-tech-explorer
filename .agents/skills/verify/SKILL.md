---
name: verify
description: Verify nasa-tech-explorer changes end-to-end — lint, local tests, fixture-built site, live smoke.
---

# Verifying nasa-tech-explorer

1. `source .venv/bin/activate && pip install -e ".[dev]"`
2. Lint exactly as CI does: `ruff format --check . && ruff check . && pylint src/`
3. Local test suite (tests/ is local-only, never committed): `pytest tests/ -q`
4. Build the real site from committed data and eyeball it:
   `python -m t2_explorer build && python -m http.server 8123 --directory site`
   — search for "strayton", click through to a detail page, check the official link.
5. Live smoke (network, optional):

   ```bash
   T2_LIVE=1 python - <<'EOF'
   from t2_explorer.api import T2Client
   rows = T2Client().fetch("patent", "rocket")
   assert rows and len(rows[0]) == 13, len(rows[0])
   print("live ok:", len(rows), "rows")
   EOF
   ```

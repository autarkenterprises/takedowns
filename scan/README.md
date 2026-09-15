# Catalog ingest (`scan/`)

Python gates for the Takedowns catalog. **Discovery** is a Cursor Cloud Agent
using Cursor’s native model. This package only **ingests** that
agent’s JSON: validate, Wayback-archive, append-only write to:

- `../README.md` — markdown table rows
- `../instances.txt` — plaintext list

Prior catalog content is preserved as an **exact prefix**. Design:
[docs/adr/0001-recurring-catalog-scanner.md](../docs/adr/0001-recurring-catalog-scanner.md).

## Standards

- **Include:** ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclude:** manufacturing tutorials, threats, illegal sales.
- **Cite + archive:** http(s) sources required; Wayback mirrors attached before write.
- **Dedup:** known entities/sources from `instances.txt` are not re-added.

## Production (Cursor Cloud via CLI)

Cursor Automations cannot be created from the API (route 404). Launch a Cloud
Agent with a User API Key (export `CURSOR_API_KEY`, or put it in gitignored
`content_scan_api_key.txt` at the repo root):

```bash
./scan/scripts/launch_cloud_agent.sh
```

The Cursor GitHub App must be installed on `autarkenterprises` with access to
this repo: https://github.com/apps/cursor/installations/new?target_id=17556938
(or Dashboard → Integrations → GitHub). Daily trigger: GitHub Actions
`.github/workflows/daily-cloud-scan.yml` (`0 12 * * *` UTC). Details:
[docs/cursor-cloud-daily-scan.md](../docs/cursor-cloud-daily-scan.md).

## Local ingest

```bash
cd scan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m takedowns_scan.cli --from-json path/to/inbox.json
```

Optional debug UI (JSON upload only):

```bash
export PYTHONPATH=src
uvicorn takedowns_scan.web:app --host 127.0.0.1 --port 8765
```

## Tests

```bash
cd scan
source .venv/bin/activate
pytest -q
```

## Environment

| Variable | Purpose |
|----------|---------|
| `SCAN_CATALOG` | Path to `instances.txt` |
| `SCAN_README` | Path to `README.md` |
| `SCAN_ADMIN_TOKEN` | Optional shared secret for the debug ingest form |

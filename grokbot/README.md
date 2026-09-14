# Catalog ingest (`grokbot/`)

Python gates for the Takedowns catalog. **Discovery** is a Cursor Cloud Agent
Automation using Cursor’s native model. This package only **ingests** that
agent’s JSON: validate, Wayback-archive, append-only write to:

- `../README.md` — markdown table rows
- `../instances.txt` — plaintext list

Prior catalog content is preserved as an **exact prefix**. Design:
[docs/adr/0001-grokbot-recurring-scanner.md](../docs/adr/0001-grokbot-recurring-scanner.md).

## Standards

- **Include:** ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclude:** manufacturing tutorials, threats, illegal sales.
- **Cite + archive:** http(s) sources required; Wayback mirrors attached before write.
- **Dedup:** known entities/sources from `instances.txt` are not re-added.

## Production (Cursor Cloud)

See [docs/cursor-cloud-daily-scan.md](../docs/cursor-cloud-daily-scan.md).

The Automation writes `grokbot/data/inbox.json`, then:

```bash
./grokbot/scripts/run_scan.sh grokbot/data/inbox.json
```

No `XAI_API_KEY`. No Grok API.

## Local ingest

```bash
cd grokbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m takedowns_grokbot.cli --from-json path/to/inbox.json
```

Optional debug UI (JSON upload only):

```bash
export PYTHONPATH=src
uvicorn takedowns_grokbot.web:app --host 127.0.0.1 --port 8765
```

## Tests

```bash
cd grokbot
source .venv/bin/activate
pytest -q
```

## Environment

| Variable | Purpose |
|----------|---------|
| `GROKBOT_CATALOG` | Path to `instances.txt` |
| `GROKBOT_README` | Path to `README.md` |
| `GROKBOT_ADMIN_TOKEN` | Optional shared secret for the debug ingest form |

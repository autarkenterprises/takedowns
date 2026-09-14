# GrokBot

Web agent that **regularly scans** for firearms content-creator suppression /
censorship and **appends validated findings** to the parent catalog:

- `../README.md` — markdown table rows (new dated GrokBot section)
- `../instances.txt` — plaintext list entries

Prior catalog content is preserved as an **exact prefix** (append-only; no
rewrite of historical rows). Design: [docs/adr/0001-grokbot-recurring-scanner.md](../docs/adr/0001-grokbot-recurring-scanner.md).

## Standards

- **Include:** ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclude:** manufacturing tutorials, threats, illegal sales.
- **Cite + archive:** http(s) sources required; Wayback mirrors attached before write.
- **Dedup:** known entities/sources from `instances.txt` are not re-added.

## Setup

```bash
cd takedowns/grokbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set XAI_API_KEY=...
```

## Launch from Cursor

1. Open the `takedowns` folder (or the parent `gcs` workspace).
2. Open the integrated terminal (**Terminal → New Terminal**).
3. Run:

```bash
cd /home/jpt4/business/gcs/takedowns/grokbot
source .venv/bin/activate
export PYTHONPATH=src
# Optional while developing: export GROKBOT_ENABLE_SCHEDULER=0
uvicorn takedowns_grokbot.web:app --host 127.0.0.1 --port 8765
```

4. In Cursor’s Simple Browser or your OS browser, open **http://127.0.0.1:8765/**
5. Click **Run scan now** (or wait for the daily scheduler).
6. Review git diff on `README.md` / `instances.txt` — new GrokBot sections only; older batches untouched.

One-off scan without the UI:

```bash
cd /home/jpt4/business/gcs/takedowns/grokbot
source .venv/bin/activate
export PYTHONPATH=src
python -m takedowns_grokbot.cli
```

## Tests

```bash
cd takedowns/grokbot
source .venv/bin/activate
pytest -q
```

Default tests use a mock Grok client and a fake archiver (no network / no API key).

## Environment

| Variable | Purpose |
|----------|---------|
| `XAI_API_KEY` | Required for live scans |
| `GROKBOT_MODEL` | Default `grok-4-1-fast-reasoning` |
| `GROKBOT_INTERVAL_HOURS` | Scheduler period (default `24`) |
| `GROKBOT_ENABLE_SCHEDULER` | Set `0` to disable background scans |
| `GROKBOT_ADMIN_TOKEN` | Optional shared secret for **Run scan now** |
| `GROKBOT_CATALOG` | Path to `instances.txt` |
| `GROKBOT_README` | Path to `README.md` |

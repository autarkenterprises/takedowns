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

## Launch on Cursor Cloud (production schedule)

Daily scans run as a **Cursor Cloud Agent Automation** (cron), not on a laptop.
See [docs/cursor-cloud-daily-scan.md](../docs/cursor-cloud-daily-scan.md).

1. Store `XAI_API_KEY` in [Cloud Agent secrets](https://cursor.com/dashboard/cloud-agents).
2. Create the Automation at [cursor.com/automations](https://cursor.com/automations): repo `autarkenterprises/takedowns`, branch `master`, cron `0 12 * * *` (UTC), prompt from that doc.
3. Each run executes `./grokbot/scripts/run_scan.sh` and pushes append-only catalog updates.

## Optional local UI (debug only)

```bash
cd grokbot
source .venv/bin/activate
export PYTHONPATH=src
# Scheduler stays off unless you explicitly export GROKBOT_ENABLE_SCHEDULER=1
uvicorn takedowns_grokbot.web:app --host 127.0.0.1 --port 8765
```

One-off scan without the UI (still needs `XAI_API_KEY`):

```bash
./grokbot/scripts/run_scan.sh
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
| `GROKBOT_ENABLE_SCHEDULER` | Local UI only; default `0` (Cloud cron is the schedule) |
| `GROKBOT_ADMIN_TOKEN` | Optional shared secret for **Run scan now** |
| `GROKBOT_CATALOG` | Path to `instances.txt` |
| `GROKBOT_README` | Path to `README.md` |

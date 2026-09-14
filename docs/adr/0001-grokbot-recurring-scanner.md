# ADR 0001: Recurring scanner for firearms-creator suppression

## Status

Accepted (amended 2026-09-14: catalog write path; Cursor Cloud cron; native Cursor model for discovery)

## Context

The `takedowns/` catalog documents platform bans, deplatformings, and demonetizations of lawful firearms content creators and brands. Manual research produced three batches under a fixed bar:

- **Inclusion:** punishment for ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclusion:** manufacturing tutorials, threats, illegal sales, and other clear criminal facilitation.
- **Evidence:** every instance needs citable public sources; source URLs are paired with Wayback Machine mirrors.
- **Ranking signal:** prefer **recency × audience size**; omit cases that fail the significance/citability bar rather than padding the list.

We want recurring discovery that writes validated findings into both `README.md` (tables) and `instances.txt` (list) without regressing prior catalog work. Discovery must run on **Cursor Cloud Agent Automations**, using **whatever model Cursor provides for that Automation**, not a third-party Grok/xAI API call.

## Decision

Split the pipeline:

1. **Discovery (Cursor native):** A daily Cloud Agent Automation uses Cursor’s Automation model and built-in tools (web search / browsing) to propose new catalog rows. It writes `{"candidates": [...]}` JSON. It does **not** call the xAI Grok API.
2. **Publication (deterministic Python):** `grokbot/scripts/run_scan.sh <inbox.json>` validates, Wayback-archives, and **append-only** writes `README.md` + `instances.txt` (prior bytes remain an exact prefix). Rejected drafts are queued for audit only.
3. **Schedule:** cron Automation on Cursor Cloud (`0 12 * * *` UTC unless changed), repo `autarkenterprises/takedowns`, branch `master`. No laptop process, no in-process APScheduler, no `XAI_API_KEY`.
4. Optional local FastAPI is debug ingest of the same JSON, not a discovery engine.

## Options considered

| Option | Why rejected / deferred |
|--------|-------------------------|
| xAI Grok API as the scan engine | Replaced: Automations already supply a Cursor-native model. |
| Draft-only queue with no catalog writes | The agent must update the table and list. |
| Full-file regenerate / re-rank all rows | Risks regressing prior wording, archives, and ordering. |
| Laptop uvicorn + APScheduler as the cron | Machine is off; production is Cursor Cloud Automations. |
| Cloud Agent edits markdown by hand | Prefix-preserving writer + validator stay in tested code. |

## Success criteria

- Unit tests prove append-only writes and JSON ingest (no network, no xAI).
- Validator + archive gates run before any catalog mutation.
- Cloud Automation prompt documents native Cursor discovery + ingest script.
- Empty `candidates` list is a successful no-op (no commit).

## Failure criteria

- Live scans invent uncited entities or sources that do not resolve.
- Writer rewrites or reorders historical rows.
- Automation is created with “no repository” so it cannot edit the catalog.

## Consequences

- Catalog files are live outputs; git history is the undo path.
- Credibility still depends on validator + citation/archive gates.
- Operators must create/update the Automation at cursor.com/automations (cannot be fully scripted from this repo).
- No xAI secret is required.

## Outcome

_Leave blank until after initial operational period; then link AAR under `docs/adr/aar/`._

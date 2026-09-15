# ADR 0001: Recurring scanner for firearms-creator suppression

## Status

Accepted (amended 2026-09-15: catalog-scanner identity and Cloud Agents API schedule; 2026-09-14: catalog write path; Cursor Cloud; native Cursor model for discovery)

## Context

The `takedowns/` catalog documents platform bans, deplatformings, and demonetizations of lawful firearms content creators and brands. Manual research produced three batches under a fixed bar:

- **Inclusion:** punishment for ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclusion:** manufacturing tutorials, threats, illegal sales, and other clear criminal facilitation.
- **Evidence:** every instance needs citable public sources; source URLs are paired with Wayback Machine mirrors.
- **Ranking signal:** prefer **recency × audience size**; omit cases that fail the significance/citability bar rather than padding the list.

We want recurring discovery that writes validated findings into both `README.md` (tables) and `instances.txt` (list) without regressing prior catalog work. Discovery runs as a **Cursor Cloud Agent** using the account’s native model and built-in web tools. Deterministic Python under `scan/` validates, archives, and appends.

## Decision

Split the pipeline:

1. **Discovery (Cursor Cloud Agent):** A daily Cloud Agent uses Cursor’s default model and built-in tools (web search / browsing) to propose new catalog rows. It writes `{"candidates": [...]}` JSON into `scan/data/inbox.json`.
2. **Publication (deterministic Python):** `scan/scripts/run_scan.sh <inbox.json>` validates, Wayback-archives, and **append-only** writes `README.md` + `instances.txt` (prior bytes remain an exact prefix). Rejected drafts are queued for audit only.
3. **Schedule:** GitHub Actions cron (`0 12 * * *` UTC unless changed) calls `POST https://api.cursor.com/v1/agents` via `takedowns_scan.cloud_launch`. Cursor Automations (`/v1/automations`) have no public create API. Repo `autarkenterprises/takedowns`, branch `master`. No laptop process and no in-process APScheduler.
4. Optional local FastAPI is debug ingest of the same JSON, not a discovery engine.

## Options considered

| Option | Why rejected / deferred |
|--------|-------------------------|
| Third-party LLM API as the scan engine | Cloud Agents already supply a Cursor-native model. |
| Draft-only queue with no catalog writes | The agent must update the table and list. |
| Full-file regenerate / re-rank all rows | Risks regressing prior wording, archives, and ordering. |
| Laptop uvicorn + APScheduler as the cron | Machine is off; production is Cursor Cloud Agents. |
| Cloud Agent edits markdown by hand | Prefix-preserving writer + validator stay in tested code. |
| Create a Cursor Automation from this repo’s CLI | `GET`/`POST /v1/automations` returns 404; schedule the Cloud Agents API instead. |

## Success criteria

- Unit tests prove append-only writes and JSON ingest (no network).
- Validator + archive gates run before any catalog mutation.
- Cloud Agent prompt documents native Cursor discovery plus the ingest script.
- Empty `candidates` list is a successful no-op (no commit).

## Failure criteria

- Live scans invent uncited entities or sources that do not resolve.
- Writer rewrites or reorders historical rows.
- Agent is launched with no repository so it cannot edit the catalog.

## Consequences

- Catalog files are live outputs; git history is the undo path.
- Credibility still depends on validator + citation/archive gates.
- Operators launch with `./scan/scripts/launch_cloud_agent.sh` (`CURSOR_API_KEY` or gitignored `content_scan_api_key.txt`). Store the same key as a GitHub Actions secret. The Cursor GitHub App must be installed on `autarkenterprises` with access to this repo.
- Package identity is `takedowns_scan` under `scan/` (not a third-party bot brand).

## Outcome

_Leave blank until after initial operational period; then link AAR under `docs/adr/aar/`._

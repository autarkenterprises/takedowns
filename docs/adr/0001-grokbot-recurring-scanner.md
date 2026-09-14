# ADR 0001: GrokBot recurring scanner for firearms-creator suppression

## Status

Accepted (amended 2026-09-14: catalog write path; Cursor Cloud cron)

## Context

The `takedowns/` catalog documents platform bans, deplatformings, and demonetizations of lawful firearms content creators and brands. Manual research produced three batches under a fixed bar:

- **Inclusion:** punishment for ordinary lawful firearms content (reviews, sport photos, brand pages, range demos).
- **Exclusion:** manufacturing tutorials, threats, illegal sales, and other clear criminal facilitation.
- **Evidence:** every instance needs citable public sources; source URLs are paired with Wayback Machine mirrors.
- **Ranking signal:** prefer **recency × audience size**; omit cases that fail the significance/citability bar rather than padding the list.

Manual scanning does not keep pace with ongoing enforcement. We want a **Grok-powered web instance** that regularly searches for new candidate instances, and **writes validated findings into both `README.md` (tables) and `instances.txt` (list)** without regressing prior catalog work.

## Decision

Build **GrokBot** as a small Python web service under `takedowns/grokbot/` that:

1. **Discovers** candidates via a CLI scan (`grokbot/scripts/run_scan.sh`); optional FastAPI UI can trigger the same path for debug.
2. **Uses the xAI Grok API** with server-side **web_search** (and optionally **x_search**) to find candidate events.
3. **Applies a deterministic validator** (code, not model judgment alone) that rejects candidates missing required fields, lacking http(s) citations, matching known catalog entities, or failing explicit exclusion heuristics.
4. **Archives source URLs** via Wayback (reuse or save) before publication.
5. **Appends accepted findings** to both `README.md` and `instances.txt` using an **append-only writer** that:
   - continues numbering from the highest existing entry;
   - adds a dated GrokBot batch section/table in the README;
   - **preserves all prior file bytes as an unchanged prefix** (no rewrite of historical rows);
   - refuses to write if that prefix check would fail.
6. **Records** queue/run artifacts under `grokbot/data/` for audit; the catalog files are the publication surface.
7. **Schedules on Cursor Cloud**, not a laptop: a daily Cloud Agent Automation (cron) clones this GitHub repo, runs `grokbot/scripts/run_scan.sh`, and pushes append-only catalog commits. Optional local FastAPI is debug-only; in-process APScheduler is off by default. Secrets (`XAI_API_KEY`) live in Cursor Cloud Agent secrets, never in git.

## Options considered

| Option | Why rejected / deferred |
|--------|-------------------------|
| Draft-only queue with no catalog writes | Rejected after product requirement: the agent must update the table and list. |
| Full-file regenerate / re-rank all rows | Risks regressing prior wording, archives, and ordering. |
| Pure RSS/keyword scrapers without an LLM | High false positives; weak narrative fit vs reporting patterns. |
| Laptop `uvicorn` + APScheduler as the cron | The machine is off; production schedule is Cursor Cloud Automations. |
| Hosted 24/7 FastAPI on Cursor VMs | Cloud agent VMs are ephemeral; cron launches a scan then exits. |

## Success criteria

- Unit tests prove append-only writes: previous README/instances content remains an exact prefix after inserts.
- Validator + archive gates run before any catalog mutation.
- Mock-client scan can append a new numbered entry to both files without altering earlier entries.
- With `XAI_API_KEY` in Cursor Cloud secrets, a Cloud Automation can run the CLI daily and append catalog rows or complete with zero publishes.
- Rejected candidates record machine-readable reasons and do not touch the catalog.

## Failure criteria

- Live scans invent uncited entities or sources that do not resolve.
- Writer rewrites or reorders historical rows → supersede with a stricter lockfile/hash gate.
- API cost makes daily scans impractical → narrower search ADR.

## Consequences

- Catalog files become live outputs of the agent; git history is the undo path.
- Credibility still depends on validator + citation/archive gates; human review of git diffs remains recommended.
- Requires an xAI API key in Cursor Cloud secrets for live mode; CI uses mocks and does not call the network.
- Daily cadence is a Cursor Automation (cron UTC); in-process APScheduler stays off unless explicitly enabled for local debug.

## Outcome

_Leave blank until after initial operational period; then link AAR under `docs/adr/aar/`._

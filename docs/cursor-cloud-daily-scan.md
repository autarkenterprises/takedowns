# Cursor Cloud daily scan

GrokBot’s scheduled runs belong on **Cursor Cloud Agents**, not a laptop
`uvicorn` process. Cloud VMs are ephemeral; a 24/7 FastAPI server is not
hosted here. The daily job is a **cron Automation** that clones this repo,
runs the scanner CLI, and pushes append-only catalog updates.

## Secrets

Add `XAI_API_KEY` at [Cloud Agents secrets](https://cursor.com/dashboard/cloud-agents)
so Automation runs receive it. Do not put the key in the prompt or in git.

## Create the Automation

1. Open [cursor.com/automations](https://cursor.com/automations) (or Agents Window → Automations).
2. Trigger: **Scheduled** cron `0 12 * * *` (12:00 UTC daily). Adjust if you prefer another hour; cron is UTC unless the UI documents otherwise.
3. Repository: **this repo** (`autarkenterprises/takedowns`), branch **`master`**. Cron defaults to *no repository* — you must attach the repo or the agent cannot edit the catalog.
4. Environment: use the repo’s `.cursor/environment.json` (do **not** skip install / “No Environment”, or secrets will not inject).
5. Tools: allow git push to the connected GitHub remote. Disable “always open a pull request” if the UI offers it; this project merges locally then pushes `master`.
6. Prompt: paste the block below.
7. Save and activate. Run once manually to confirm `XAI_API_KEY` is present (`test -n "$XAI_API_KEY" && echo present`).

## Automation prompt

```
You are the daily Takedowns GrokBot scan on Cursor Cloud.

1. Read AGENTS.md and grokbot/README.md.
2. If XAI_API_KEY is unset, stop and report; do not invent catalog rows.
3. Run ./grokbot/scripts/run_scan.sh from the repo root.
4. The scanner writes append-only sections to README.md and instances.txt after citation + Wayback gates. Never rewrite historical rows.
5. If those files changed: commit only README.md and instances.txt, fast-forward into master, and push to GitHub. Do not open a pull request as the merge gate.
6. If nothing changed, do not commit.
7. Reply with the scan report JSON (discovered / accepted / rejected) and whether you pushed.
```

## Optional local UI

`uvicorn` on a workstation is debug-only. Leave `GROKBOT_ENABLE_SCHEDULER=0`
(the default) so a laptop cannot become a competing cron.

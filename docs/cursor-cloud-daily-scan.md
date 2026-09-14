# Cursor Cloud daily scan

Discovery uses **Cursor’s native Cloud Agent Automation model**, not Grok/xAI.
The Python tree only **ingests** the agent’s JSON (validate + Wayback +
append-only catalog write). Cloud VMs are ephemeral; there is no 24/7 server.

## Secrets

None required for discovery. Do **not** add `XAI_API_KEY`.

## Create or update the Automation

1. Open [cursor.com/automations](https://cursor.com/automations).
2. Trigger: **Scheduled** cron `0 12 * * *` (12:00 UTC daily).
3. Repository: **this repo** (`autarkenterprises/takedowns`), branch **`master`**.
   Cron defaults to *no repository* — attach the repo or the agent cannot edit files.
4. Model: leave the Automation default (Cursor-native). Do not configure Grok/xAI.
5. Environment: repo `.cursor/environment.json` (do not skip install).
6. Tools: git push to GitHub. Disable “always open a pull request” if offered.
7. Prompt: paste the block below. Save, activate, run once by hand.

## Automation prompt

```
You are the daily Takedowns catalog scan on Cursor Cloud.

Use Cursor’s native model and web tools. Do not call xAI, Grok, or any XAI_API_KEY.

1. Read AGENTS.md, README.md, and instances.txt.
2. Search for NEW platform punishments of firearms creators/brands for ordinary
   lawful content (reviews, sport photos, brand pages, range demos). Exclude
   manufacturing tutorials, threats, and illegal sales. Prefer recency × audience.
   Do not invent sources. Omit cases that fail the bar.
3. Write grokbot/data/inbox.json as {"candidates":[...]} matching AGENTS.md.
   Use {"candidates":[]} if none qualify.
4. Run ./grokbot/scripts/run_scan.sh grokbot/data/inbox.json
5. If README.md or instances.txt changed: commit only those files, fast-forward
   master, push to GitHub. Do not open a pull request as the merge gate.
6. If nothing changed, do not commit.
7. Reply with ingest report JSON (discovered / accepted / rejected) and whether you pushed.
```

## Optional local ingest UI

Debug-only: upload the same JSON to the FastAPI ingest form. Production cadence
is the Cloud Automation, not a laptop process.

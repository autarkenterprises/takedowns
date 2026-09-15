# Cursor Cloud daily scan

Discovery uses a **Cursor Cloud Agent** running **Grok 4.6 High Fast**.
Python only **ingests** the agent’s JSON.

## Why not cursor.com/automations from CLI

`GET`/`POST https://api.cursor.com/v1/automations` returns **404**. There is no
public API or `agent` CLI command that creates an Automation. A Cursor CLI
login token is also **not** a User API Key (`Invalid User API Key`).

The supported CLI setup is:

1. `POST /v1/agents` (Cloud Agents API) — agent runs on Cursor VMs
2. GitHub Actions cron `0 12 * * *` — only the trigger; not the worker

## One-time CLI setup

1. Create a **User API Key** at [cursor.com/dashboard/api](https://cursor.com/dashboard/api).
2. Either export it or write it to gitignored `content_scan_api_key.txt` at the repo root (do not commit it).
3. Install the **Cursor GitHub App** on org `autarkenterprises` and grant `takedowns` (or All repositories): [github.com/apps/cursor](https://github.com/apps/cursor/installations/new?target_id=17556938). Confirm GitHub is connected at [Integrations](https://cursor.com/dashboard?tab=integrations).
4. Launch one Cloud Agent:

```bash
./scan/scripts/launch_cloud_agent.sh
```

5. Store the same key as a GitHub Actions secret so the daily cron can fire:

```bash
gh secret set CURSOR_API_KEY -R autarkenterprises/takedowns < content_scan_api_key.txt
```

The workflow is [`.github/workflows/daily-cloud-scan.yml`](../.github/workflows/daily-cloud-scan.yml). Manual run: Actions → daily-cloud-scan → Run workflow.

## Agent prompt

[`scan/cloud_prompt.txt`](../scan/cloud_prompt.txt) is what every launch sends.

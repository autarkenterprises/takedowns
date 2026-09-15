# Cursor Cloud daily scan

Discovery uses **Cursor’s native Cloud Agent** (account default model).
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
2. Export it (do not commit it):

```bash
export CURSOR_API_KEY='…'
```

3. Launch one Cloud Agent now:

```bash
./scan/scripts/launch_cloud_agent.sh
```

4. Store the same key as a GitHub Actions secret so the daily cron can fire:

```bash
gh secret set CURSOR_API_KEY -R autarkenterprises/takedowns
```

The workflow is [`.github/workflows/daily-cloud-scan.yml`](../.github/workflows/daily-cloud-scan.yml). Manual run: Actions → daily-cloud-scan → Run workflow.

## Agent prompt

[`scan/cloud_prompt.txt`](../scan/cloud_prompt.txt) is what every launch sends.

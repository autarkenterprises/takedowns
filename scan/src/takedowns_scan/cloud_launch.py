"""
Launch a Cursor Cloud Agent for one catalog scan (native Cursor model).

Cursor Automations (cursor.com/automations) have no public create API — probed
GET/POST /v1/automations → 404. The supported CLI path is Cloud Agents API
POST /v1/agents. Daily cadence is an external cron (GitHub Actions in this
repo) that calls this launcher; the agent itself still runs on Cursor VMs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.cursor.com/v1/agents"
REPO_URL = "https://github.com/autarkenterprises/takedowns"
DEFAULT_REF = "master"

ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "cloud_prompt.txt"


def load_prompt(path: Path = PROMPT_PATH) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"empty prompt file: {path}")
    return text


def build_create_payload(prompt: str, starting_ref: str = DEFAULT_REF) -> dict[str, Any]:
    """Request body for POST /v1/agents. Omit model so Cursor uses the account default."""
    return {
        "name": "takedowns-daily-scan",
        "prompt": {"text": prompt},
        "repos": [{"url": REPO_URL, "startingRef": starting_ref}],
        "autoCreatePR": False,
    }


def create_agent(api_key: str, payload: dict[str, Any], timeout_sec: int = 60) -> dict[str, Any]:
    """POST /v1/agents. api_key is a User API Key from cursor.com/dashboard/api."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"Cloud Agents API HTTP {exc.code}: {detail}") from exc


def agent_dashboard_url(response: dict[str, Any]) -> str:
    """Prefer API-provided URL; fall back to id-based agents page."""
    for key in ("url", "targetUrl", "target"):
        val = response.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
    agent = response.get("agent") or {}
    if isinstance(agent, dict):
        for key in ("url", "targetUrl"):
            val = agent.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
        agent_id = agent.get("id") or response.get("id")
    else:
        agent_id = response.get("id")
    if agent_id:
        return f"https://cursor.com/agents?id={agent_id}"
    return "https://cursor.com/agents"


def main() -> int:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "CURSOR_API_KEY is unset. Create a User API Key at "
            "https://cursor.com/dashboard/api and export it. "
            "(CLI `agent login` session tokens are not accepted by this API.)"
        )
    payload = build_create_payload(load_prompt())
    result = create_agent(key, payload)
    summary = {
        "id": (result.get("agent") or {}).get("id") or result.get("id"),
        "url": agent_dashboard_url(result),
        "status": result.get("status") or (result.get("agent") or {}).get("status"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

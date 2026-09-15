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
from typing import Any, Mapping

API = "https://api.cursor.com/v1/agents"
REPO_URL = "https://github.com/autarkenterprises/takedowns"
DEFAULT_REF = "master"
# Public GitHub org id for autarkenterprises (install target, not a secret).
GITHUB_ORG_ID = 17556938
GITHUB_APP_INSTALL = (
    f"https://github.com/apps/cursor/installations/new?target_id={GITHUB_ORG_ID}"
)
INTEGRATIONS_URL = "https://cursor.com/dashboard?tab=integrations"

# scan/src/takedowns_scan/cloud_launch.py → repo root is parents[3].
ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = ROOT / "cloud_prompt.txt"
KEY_FILE = REPO_ROOT / "content_scan_api_key.txt"


def load_prompt(path: Path = PROMPT_PATH) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"empty prompt file: {path}")
    return text


def resolve_api_key(
    env: Mapping[str, str] | None = None,
    key_file: Path = KEY_FILE,
) -> str:
    """
    Prefer CURSOR_API_KEY (CI / explicit export). Fall back to the gitignored
    local file operators drop at the repo root.
    """
    mapping = os.environ if env is None else env
    key = (mapping.get("CURSOR_API_KEY") or "").strip()
    if key:
        return key
    if key_file.is_file():
        text = key_file.read_text(encoding="utf-8").strip()
        if text:
            return text
    raise SystemExit(
        "CURSOR_API_KEY is unset and content_scan_api_key.txt is missing. "
        "Create a User API Key at https://cursor.com/dashboard/api and either "
        "export it or write it to content_scan_api_key.txt (gitignored). "
        "(CLI `agent login` session tokens are not accepted by this API.)"
    )


def build_create_payload(prompt: str, starting_ref: str = DEFAULT_REF) -> dict[str, Any]:
    """Request body for POST /v1/agents. Omit model so Cursor uses the account default."""
    return {
        "name": "takedowns-daily-scan",
        "prompt": {"text": prompt},
        "repos": [{"url": REPO_URL, "startingRef": starting_ref}],
        "autoCreatePR": False,
        # Catalog writes land on master (AGENTS.md); do not fork a cursor/* branch.
        "workOnCurrentBranch": True,
    }


def format_create_error(code: int, detail: str) -> str:
    """Attach operator next-steps when Cursor cannot see the GitHub repo."""
    msg = f"Cloud Agents API HTTP {code}: {detail}"
    scm = (
        "repository_access" in detail
        or "does not have access to repository" in detail
        or "Failed to verify existence of branch" in detail
    )
    if not scm:
        return msg
    return (
        f"{msg}\n"
        "Cursor's GitHub App cannot see autarkenterprises/takedowns. "
        f"Install it on the org ({GITHUB_APP_INSTALL}) and grant this repo "
        f"(or All repositories). Confirm GitHub is connected at {INTEGRATIONS_URL}."
    )


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
        raise RuntimeError(format_create_error(exc.code, detail)) from exc


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
    payload = build_create_payload(load_prompt())
    result = create_agent(resolve_api_key(), payload)
    summary = {
        "id": (result.get("agent") or {}).get("id") or result.get("id"),
        "url": agent_dashboard_url(result),
        "status": result.get("status") or (result.get("agent") or {}).get("status"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

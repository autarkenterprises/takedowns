"""Tests for Cloud Agents API payload construction (no network)."""

from takedowns_scan.cloud_launch import (
    REPO_URL,
    agent_dashboard_url,
    build_create_payload,
)


def test_payload_uses_native_default_model_and_no_pr():
    payload = build_create_payload("scan now", starting_ref="master")
    assert "model" not in payload  # Cursor account/automation default
    assert payload["autoCreatePR"] is False
    assert payload["repos"] == [{"url": REPO_URL, "startingRef": "master"}]
    assert payload["prompt"]["text"] == "scan now"
    assert payload["name"] == "takedowns-daily-scan"


def test_dashboard_url_from_nested_agent():
    url = agent_dashboard_url({"agent": {"id": "bc-abc"}})
    assert "bc-abc" in url
    assert url.startswith("https://cursor.com/agents")

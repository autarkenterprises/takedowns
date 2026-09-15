"""Tests for Cloud Agents API payload construction and local key loading (no network)."""

from pathlib import Path

import pytest

from takedowns_scan.cloud_launch import (
    REPO_URL,
    agent_dashboard_url,
    build_create_payload,
    format_create_error,
    resolve_api_key,
)


def test_payload_uses_native_default_model_and_no_pr():
    payload = build_create_payload("scan now", starting_ref="master")
    assert "model" not in payload  # Cursor account/automation default
    assert payload["autoCreatePR"] is False
    assert payload["workOnCurrentBranch"] is True
    assert payload["repos"] == [{"url": REPO_URL, "startingRef": "master"}]
    assert payload["prompt"]["text"] == "scan now"
    assert payload["name"] == "takedowns-daily-scan"


def test_dashboard_url_from_nested_agent():
    url = agent_dashboard_url({"agent": {"id": "bc-abc"}})
    assert "bc-abc" in url
    assert url.startswith("https://cursor.com/agents")


def test_resolve_api_key_prefers_environment(tmp_path: Path):
    key_file = tmp_path / "content_scan_api_key.txt"
    key_file.write_text("file-key\n", encoding="utf-8")
    got = resolve_api_key(env={"CURSOR_API_KEY": " env-key "}, key_file=key_file)
    assert got == "env-key"


def test_resolve_api_key_reads_local_file(tmp_path: Path):
    key_file = tmp_path / "content_scan_api_key.txt"
    key_file.write_text("file-only-key\n", encoding="utf-8")
    got = resolve_api_key(env={}, key_file=key_file)
    assert got == "file-only-key"


def test_resolve_api_key_missing_exits(tmp_path: Path):
    with pytest.raises(SystemExit):
        resolve_api_key(env={}, key_file=tmp_path / "missing.txt")


def test_format_create_error_explains_missing_github_app():
    detail = (
        '{"error":{"code":"repository_access","message":'
        '"The SCM integration does not have access to repository '
        'autarkenterprises/takedowns."}}'
    )
    text = format_create_error(400, detail)
    assert "github.com/apps/cursor" in text
    assert "autarkenterprises/takedowns" in text
    assert "repository_access" in text

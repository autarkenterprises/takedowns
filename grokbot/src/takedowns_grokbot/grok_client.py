"""
xAI Grok client for candidate discovery (web_search / optional x_search).

Live calls require XAI_API_KEY. Tests use FakeGrokClient instead.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from takedowns_grokbot.models import CandidateDraft


SYSTEM_PROMPT = """You are a research assistant for a curated catalog of platform
bans, deplatformings, and demonetizations affecting firearms content creators
and brands.

STRICT INCLUSION: punishment for ordinary lawful firearms content (reviews,
sport photos, brand pages, range demos).

STRICT EXCLUSION: manufacturing tutorials, threats of violence, illegal sales,
or other clear criminal facilitation.

STANDARDS:
- Only propose NEW entities not already listed in the known-catalog summary.
- Every candidate MUST include at least one real http(s) news/primary URL.
- Prefer recency × audience size; omit weak or uncitable cases rather than pad.
- Do not invent sources. If you cannot cite, return an empty candidates list.
- Return ONLY JSON matching the schema described by the user.
"""


USER_PROMPT_TEMPLATE = """Known catalog summary:
{known_summary}

Search the public web (and X if available) for NEW instances since the most
recent catalog coverage of firearms creators/brands punished for ordinary
lawful gun content on YouTube, Meta/Instagram/Facebook, TikTok, or similar.

Return JSON of the form:
{{
  "candidates": [
    {{
      "who": "string",
      "audience": "string",
      "when": "string",
      "platform": "string",
      "what_happened": "string",
      "content_description": "string",
      "sources": ["https://..."],
      "fit_rationale": "string",
      "confidence": 0.0
    }}
  ]
}}

If none meet the bar, return {{"candidates": []}}.
"""


class GrokClient:
    """
    Thin wrapper around the xAI Responses API with server-side web_search.

    Network I/O is isolated here so the rest of the pipeline stays testable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "grok-4-1-fast-reasoning",
        endpoint: str = "https://api.x.ai/v1/responses",
        enable_x_search: bool = True,
        timeout_sec: int = 180,
    ):
        # Prefer grok-4-1-fast-reasoning for cost on recurring scans; override via env.
        self.api_key = api_key or os.environ.get("XAI_API_KEY", "")
        self.model = os.environ.get("GROKBOT_MODEL", model)
        self.endpoint = endpoint
        self.enable_x_search = enable_x_search
        self.timeout_sec = timeout_sec

    def discover_candidates(self, known_summary: str) -> list[CandidateDraft]:
        if not self.api_key:
            raise RuntimeError(
                "XAI_API_KEY is not set. Export an xAI API key for live scans, "
                "or use a mock client in tests."
            )
        tools: list[dict[str, Any]] = [{"type": "web_search"}]
        if self.enable_x_search:
            tools.append({"type": "x_search"})

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(known_summary=known_summary),
                },
            ],
            "tools": tools,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"xAI API HTTP {exc.code}: {detail[:500]}") from exc

        data = json.loads(raw)
        text = _extract_output_text(data)
        parsed = _parse_candidates_json(text)
        return [CandidateDraft.from_dict(item) for item in parsed]


def _extract_output_text(data: dict[str, Any]) -> str:
    """
    Normalize Responses API payloads into a single text blob.

    The API shape evolves; we accept several common layouts.
    """
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]

    chunks: list[str] = []
    output = data.get("output") or data.get("choices") or []
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                if item.get("type") == "message":
                    content = item.get("content") or []
                    if isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") in (
                                "output_text",
                                "text",
                            ):
                                chunks.append(str(part.get("text") or ""))
                    elif isinstance(content, str):
                        chunks.append(content)
                msg = item.get("message") or {}
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    chunks.append(msg["content"])
                if isinstance(item.get("text"), str):
                    chunks.append(item["text"])
    if chunks:
        return "\n".join(chunks)

    # Chat Completions-like fallback
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 - intentional broad normalize
        raise RuntimeError(f"Unrecognized xAI response shape: {list(data)[:20]}") from exc


def _parse_candidates_json(text: str) -> list[dict[str, Any]]:
    """Extract the candidates array from model text (raw JSON or fenced)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    # If surrounding prose exists, grab the outermost JSON object.
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    data = json.loads(text)
    cands = data.get("candidates")
    if cands is None:
        return []
    if not isinstance(cands, list):
        raise RuntimeError("candidates field must be a list")
    return cands

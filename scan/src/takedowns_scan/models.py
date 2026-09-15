"""
Shared data models for discovery drafts and scan reports.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CandidateDraft:
    """
    Structured proposal from a Cursor Cloud Agent (or a test double) before
    the deterministic validator runs.

    Fields mirror the catalog columns so approved drafts can be pasted into
    instances.txt / README.md with minimal rewriting.
    """

    who: str
    audience: str
    when: str
    platform: str
    what_happened: str
    content_description: str
    sources: list[str]
    fit_rationale: str
    confidence: float
    archive_urls: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateDraft":
        return cls(
            who=str(data.get("who", "")).strip(),
            audience=str(data.get("audience", "")).strip(),
            when=str(data.get("when", "")).strip(),
            platform=str(data.get("platform", "")).strip(),
            what_happened=str(data.get("what_happened", "")).strip(),
            content_description=str(data.get("content_description", "")).strip(),
            sources=[str(s).strip() for s in (data.get("sources") or []) if str(s).strip()],
            fit_rationale=str(data.get("fit_rationale", "")).strip(),
            confidence=float(data.get("confidence", 0.0)),
            archive_urls={str(k): str(v) for k, v in (data.get("archive_urls") or {}).items()},
        )


def load_candidates_json(path: Path) -> list[CandidateDraft]:
    """
    Load a Cursor Cloud Agent inbox file.

    Expected shape: ``{"candidates": [ {who, audience, when, platform,
    what_happened, content_description, sources, fit_rationale, confidence} ]}``.
    An empty list is valid (no new findings).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = data.get("candidates")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("candidates field must be a list")
    return [CandidateDraft.from_dict(item) for item in raw]


@dataclass
class ScanReport:
    """Summary of one discovery pass for the UI and run logs."""

    discovered: int
    accepted: int
    rejected: int
    run_id: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

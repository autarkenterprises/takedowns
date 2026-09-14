"""
Shared data models for discovery drafts and scan reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CandidateDraft:
    """
    Structured proposal from Grok (or a fake client) before human review.

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

"""
Filesystem-backed review queue for candidate drafts.

Candidates are JSON files under a directory. The published catalog is never
modified by enqueue operations.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from takedowns_scan.models import CandidateDraft


class CandidateQueue:
    """Persist candidates as one JSON document per id."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, candidate_id: str) -> Path:
        return self.root / f"{candidate_id}.json"

    def enqueue(
        self,
        draft: CandidateDraft,
        status: str = "pending_review",
        validation_errors: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        candidate_id = uuid.uuid4().hex[:12]
        payload = {
            "id": candidate_id,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "validation_errors": validation_errors or [],
            "draft": draft.to_dict(),
            "meta": meta or {},
            "catalog_draft_text": "",
        }
        self._path(candidate_id).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return candidate_id

    def get(self, candidate_id: str) -> dict[str, Any] | None:
        path = self._path(candidate_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("status") == status:
                items.append(data)
        return items

    def list_all(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*.json"), reverse=True):
            items.append(json.loads(path.read_text(encoding="utf-8")))
        return items

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        """Overwrite a candidate document (full payload)."""
        candidate_id = data["id"]
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._path(candidate_id).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return data

    def update_status(
        self,
        candidate_id: str,
        status: str,
        catalog_draft_text: str | None = None,
        draft: CandidateDraft | None = None,
    ) -> dict[str, Any] | None:
        data = self.get(candidate_id)
        if data is None:
            return None
        data["status"] = status
        if catalog_draft_text is not None:
            data["catalog_draft_text"] = catalog_draft_text
        if draft is not None:
            data["draft"] = draft.to_dict()
        return self.save(data)


def format_instances_entry(draft: CandidateDraft, number: int) -> str:
    """Render a catalog-ready plaintext block matching instances.txt style."""
    source_lines: list[str] = []
    for i, src in enumerate(draft.sources):
        arch = draft.archive_urls.get(src, "")
        if i == 0:
            source_lines.append(f"   Sources: {src}")
        else:
            source_lines.append(f"            {src}")
        if arch:
            source_lines.append(f"            archive: {arch}")
    body = "\n".join(
        [
            f"{number}. {draft.who}",
            f"   Audience: {draft.audience}",
            f"   When: {draft.when}",
            f"   Platform: {draft.platform}",
            f"   What: {draft.what_happened}",
            *source_lines,
        ]
    )
    return body + "\n"

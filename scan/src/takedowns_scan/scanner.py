"""
Orchestrate one ingest cycle: proposed drafts → validate → archive → append.

Discovery is the Cursor Cloud Agent (Grok 4.6 High Fast). This module
only ingests already-proposed JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from takedowns_scan.archive import ensure_archives
from takedowns_scan.catalog import load_catalog_index
from takedowns_scan.catalog_writer import append_candidates
from takedowns_scan.models import CandidateDraft, ScanReport, load_candidates_json
from takedowns_scan.queue_store import CandidateQueue
from takedowns_scan.validate import validate_candidate


class DiscoveryClient(Protocol):
    def discover_candidates(self, known_summary: str) -> list[CandidateDraft]:
        ...


class StaticCandidateSource:
    """Inbox of drafts already produced by the Cursor Cloud Agent."""

    def __init__(self, drafts: list[CandidateDraft]):
        self._drafts = drafts

    @classmethod
    def from_json_file(cls, path: Path) -> "StaticCandidateSource":
        return cls(load_candidates_json(path))

    def discover_candidates(self, known_summary: str) -> list[CandidateDraft]:
        # known_summary is unused: the Cloud Agent already had the catalog.
        _ = known_summary
        return list(self._drafts)


ArchiveFn = Callable[[list[str]], dict[str, str]]


def run_scan(
    catalog_path: Path,
    queue_dir: Path,
    runs_dir: Path,
    client: DiscoveryClient,
    readme_path: Path | None = None,
    min_confidence: float = 0.55,
    archive_fn: ArchiveFn | None = None,
    write_catalog: bool = True,
) -> ScanReport:
    """
    Execute a single scan cycle.

    Accepted candidates (validator + archives) are appended to instances.txt and
    README.md without rewriting prior content. Rejected candidates are queued
    for audit only.
    """
    catalog_path = Path(catalog_path)
    readme_path = Path(readme_path) if readme_path else catalog_path.with_name("README.md")
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Snapshot prior catalog bytes for explicit non-regression checks in the report.
    prior_instances = catalog_path.read_text(encoding="utf-8") if catalog_path.exists() else ""
    prior_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

    index = load_catalog_index(catalog_path)
    known_summary = "catalog\n" + index.summary_for_prompt()
    drafts = client.discover_candidates(known_summary)

    queue = CandidateQueue(Path(queue_dir))
    accepted_drafts: list[CandidateDraft] = []
    rejected = 0
    details: list[dict] = []
    archiver = archive_fn or ensure_archives

    for draft in drafts:
        result = validate_candidate(
            draft,
            known_entities=index.entity_names,
            known_sources=index.source_urls,
            min_confidence=min_confidence,
        )
        if not result.accepted:
            rejected += 1
            cid = queue.enqueue(
                draft,
                status="rejected_auto",
                validation_errors=result.errors,
                meta={"run_id": run_id, "notes": result.notes},
            )
            details.append(
                {"id": cid, "who": draft.who, "accepted": False, "errors": result.errors}
            )
            continue

        # Archive before publish; skip catalog write if archives fail.
        try:
            archives = archiver(list(draft.sources))
        except Exception as exc:  # noqa: BLE001
            rejected += 1
            cid = queue.enqueue(
                draft,
                status="rejected_auto",
                validation_errors=["archive_failed"],
                meta={"run_id": run_id, "notes": [str(exc)]},
            )
            details.append(
                {
                    "id": cid,
                    "who": draft.who,
                    "accepted": False,
                    "errors": ["archive_failed"],
                }
            )
            continue

        missing = [s for s in draft.sources if s not in archives]
        if missing:
            rejected += 1
            cid = queue.enqueue(
                draft,
                status="rejected_auto",
                validation_errors=["archive_incomplete"],
                meta={"run_id": run_id, "missing_archives": missing},
            )
            details.append(
                {
                    "id": cid,
                    "who": draft.who,
                    "accepted": False,
                    "errors": ["archive_incomplete"],
                }
            )
            continue

        draft.archive_urls.update(archives)
        accepted_drafts.append(draft)
        cid = queue.enqueue(
            draft,
            status="published",
            validation_errors=[],
            meta={"run_id": run_id},
        )
        details.append({"id": cid, "who": draft.who, "accepted": True, "errors": []})

        # Keep index fresh within the same scan so duplicates in one batch collide.
        index.entity_names.add(draft.who.lower())
        for src in draft.sources:
            index.source_urls.add(src)

    appended = 0
    first_number = 0
    last_number = 0
    if write_catalog and accepted_drafts:
        append_result = append_candidates(readme_path, catalog_path, accepted_drafts)
        appended = append_result.added
        first_number = append_result.first_number
        last_number = append_result.last_number

    # Non-regression: prior content must remain an exact prefix.
    if catalog_path.exists():
        now_i = catalog_path.read_text(encoding="utf-8")
        if not now_i.startswith(prior_instances):
            catalog_path.write_text(prior_instances, encoding="utf-8")
            if readme_path.exists():
                readme_path.write_text(prior_readme, encoding="utf-8")
            raise RuntimeError("instances.txt prefix regression; restored prior catalogs")
    if readme_path.exists():
        now_r = readme_path.read_text(encoding="utf-8")
        if not now_r.startswith(prior_readme):
            readme_path.write_text(prior_readme, encoding="utf-8")
            catalog_path.write_text(prior_instances, encoding="utf-8")
            raise RuntimeError("README.md prefix regression; restored prior catalogs")

    report = ScanReport(
        discovered=len(drafts),
        accepted=len(accepted_drafts),
        rejected=rejected,
        run_id=run_id,
        notes=(
            f"published {appended} to catalog "
            f"(numbers {first_number}-{last_number}); auto-rejected {rejected}"
            if appended
            else f"published 0; auto-rejected {rejected}"
        ),
    )
    (runs_dir / f"{run_id}.json").write_text(
        json.dumps({"report": report.to_dict(), "details": details}, indent=2) + "\n",
        encoding="utf-8",
    )
    return report

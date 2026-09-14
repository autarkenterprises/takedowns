"""
Tests for candidate queue persistence and scanner orchestration (mock Grok).
"""

from pathlib import Path

from takedowns_grokbot.models import CandidateDraft, ScanReport
from takedowns_grokbot.queue_store import CandidateQueue
from takedowns_grokbot.scanner import run_scan


class FakeDiscoveryClient:
    """Deterministic stand-in that returns one good and one bad draft."""

    def discover_candidates(self, known_summary: str):
        assert isinstance(known_summary, str)
        return [
            CandidateDraft(
                who="Fresh Example Arms Channel",
                audience="~120K YouTube subs",
                when="Sep 2026",
                platform="YouTube",
                what_happened=(
                    "Channel terminated for ordinary range-demo videos; "
                    "platform later called it a mistake."
                ),
                content_description="range demos",
                sources=["https://press.example.com/fresh-example-arms-takedown"],
                fit_rationale="Ordinary demos; platform admitted error.",
                confidence=0.9,
            ),
            CandidateDraft(
                who="Bad Actor Builds",
                audience="small",
                when="Sep 2026",
                platform="YouTube",
                what_happened="Removed for manufacturing tutorial of illegal firearms.",
                content_description="manufacturing tutorial",
                sources=["https://press.example.com/bad-actor"],
                fit_rationale="Should be excluded.",
                confidence=0.95,
            ),
        ]


def _fake_archive(urls: list[str]) -> dict[str, str]:
    return {u: f"https://web.archive.org/web/20260101000000/{u}" for u in urls}


def test_queue_round_trip(tmp_path: Path):
    queue = CandidateQueue(tmp_path / "candidates")
    draft = CandidateDraft(
        who="Queued Creator",
        audience="~10K",
        when="2026",
        platform="YouTube",
        what_happened="Demonetized for ordinary reviews.",
        content_description="reviews",
        sources=["https://example.com/q"],
        fit_rationale="fit",
        confidence=0.7,
    )
    cid = queue.enqueue(draft, status="pending_review", validation_errors=[])
    loaded = queue.get(cid)
    assert loaded is not None
    assert loaded["draft"]["who"] == "Queued Creator"
    assert loaded["status"] == "pending_review"
    pending = queue.list_by_status("pending_review")
    assert len(pending) == 1


def test_run_scan_publishes_only_accepted_without_regressing(tmp_path: Path):
    instances = tmp_path / "instances.txt"
    readme = tmp_path / "README.md"
    prior_i = (
        "1. Already Known\n"
        "   Sources: https://example.com/known\n"
        "            archive: https://web.archive.org/web/1/https://example.com/known\n"
    )
    prior_r = (
        "# Takedowns\n\n"
        "| # | Who | Audience | When | Platform | What happened |\n"
        "|---|-----|----------|------|----------|---------------|\n"
        "| 1 | **Already Known** | n/a | 2024 | YouTube | Known. |\n"
    )
    instances.write_text(prior_i, encoding="utf-8")
    readme.write_text(prior_r, encoding="utf-8")

    report = run_scan(
        catalog_path=instances,
        readme_path=readme,
        queue_dir=tmp_path / "candidates",
        runs_dir=tmp_path / "runs",
        client=FakeDiscoveryClient(),
        archive_fn=_fake_archive,
    )
    assert isinstance(report, ScanReport)
    assert report.discovered == 2
    assert report.accepted == 1
    assert report.rejected == 1

    after_i = instances.read_text(encoding="utf-8")
    after_r = readme.read_text(encoding="utf-8")
    assert after_i.startswith(prior_i)
    assert after_r.startswith(prior_r)
    assert "2. Fresh Example Arms Channel" in after_i
    assert "| 2 |" in after_r
    assert "Fresh Example Arms Channel" in after_r
    assert "Bad Actor Builds" not in after_i
    assert "Bad Actor Builds" not in after_r

    queue = CandidateQueue(tmp_path / "candidates")
    published = queue.list_by_status("published")
    assert len(published) == 1
    assert published[0]["draft"]["who"] == "Fresh Example Arms Channel"

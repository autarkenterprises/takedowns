"""JSON inbox ingest: Cursor Cloud Agent proposes; Python validates and appends."""

from pathlib import Path

from takedowns_grokbot.models import CandidateDraft, load_candidates_json
from takedowns_grokbot.scanner import StaticCandidateSource, run_scan


def _fake_archive(urls: list[str]) -> dict[str, str]:
    return {u: f"https://web.archive.org/web/20260101000000/{u}" for u in urls}


def test_load_candidates_json_round_trip(tmp_path: Path):
    path = tmp_path / "inbox.json"
    path.write_text(
        """
        {"candidates": [
          {
            "who": "Inbox Channel",
            "audience": "~1K",
            "when": "2026",
            "platform": "YouTube",
            "what_happened": "Demonetized for ordinary reviews.",
            "content_description": "reviews",
            "sources": ["https://example.com/inbox"],
            "fit_rationale": "ordinary reviews",
            "confidence": 0.8
          }
        ]}
        """,
        encoding="utf-8",
    )
    drafts = load_candidates_json(path)
    assert len(drafts) == 1
    assert isinstance(drafts[0], CandidateDraft)
    assert drafts[0].who == "Inbox Channel"


def test_run_scan_from_static_json_source(tmp_path: Path):
    instances = tmp_path / "instances.txt"
    readme = tmp_path / "README.md"
    instances.write_text("1. Already Known\n   Sources: https://example.com/known\n", encoding="utf-8")
    readme.write_text("# Takedowns\n", encoding="utf-8")
    inbox = tmp_path / "inbox.json"
    inbox.write_text(
        '{"candidates":[{'
        '"who":"Fresh Example Arms Channel",'
        '"audience":"~120K YouTube subs",'
        '"when":"Sep 2026",'
        '"platform":"YouTube",'
        '"what_happened":"Channel terminated for ordinary range-demo videos.",'
        '"content_description":"range demos",'
        '"sources":["https://press.example.com/fresh-example-arms-takedown"],'
        '"fit_rationale":"Ordinary demos.",'
        '"confidence":0.9'
        "}]}",
        encoding="utf-8",
    )
    report = run_scan(
        catalog_path=instances,
        readme_path=readme,
        queue_dir=tmp_path / "candidates",
        runs_dir=tmp_path / "runs",
        client=StaticCandidateSource.from_json_file(inbox),
        archive_fn=_fake_archive,
    )
    assert report.accepted == 1
    assert "2. Fresh Example Arms Channel" in instances.read_text(encoding="utf-8")

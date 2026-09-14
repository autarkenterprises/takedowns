"""
Append-only catalog writer tests: never regress prior README / instances text.
"""

from pathlib import Path

from takedowns_grokbot.catalog_writer import (
    AppendResult,
    append_candidates,
    next_entry_number,
)
from takedowns_grokbot.models import CandidateDraft


README_SEED = """# Takedowns

| # | Who | Audience | When | Platform | What happened |
|---|-----|----------|------|----------|---------------|
| 1 | **Alpha** | 1M | 2024 | YouTube | Struck. [News](https://example.com/a) ([archive](https://web.archive.org/web/1/https://example.com/a)) |

Batch note.
"""

INSTANCES_SEED = """Firearms creators punished for ordinary gun content

1. Alpha
   Audience: 1M
   When: 2024
   Platform: YouTube
   What: Struck.
   Sources: https://example.com/a
            archive: https://web.archive.org/web/1/https://example.com/a
"""


def _draft(**overrides) -> CandidateDraft:
    data = dict(
        who="Beta Channel",
        audience="~50K YouTube subs",
        when="Sep 2026",
        platform="YouTube",
        what_happened="Demonetized for ordinary range demos.",
        content_description="range demos",
        sources=["https://example.com/beta"],
        fit_rationale="ordinary demos",
        confidence=0.9,
        archive_urls={
            "https://example.com/beta": "https://web.archive.org/web/9/https://example.com/beta"
        },
    )
    data.update(overrides)
    return CandidateDraft(**data)


def test_next_entry_number_from_instances(tmp_path: Path):
    path = tmp_path / "instances.txt"
    path.write_text(INSTANCES_SEED, encoding="utf-8")
    assert next_entry_number(path) == 2


def test_append_preserves_exact_prefix(tmp_path: Path):
    readme = tmp_path / "README.md"
    instances = tmp_path / "instances.txt"
    readme.write_text(README_SEED, encoding="utf-8")
    instances.write_text(INSTANCES_SEED, encoding="utf-8")
    before_r = readme.read_text(encoding="utf-8")
    before_i = instances.read_text(encoding="utf-8")

    result = append_candidates(readme, instances, [_draft()])
    assert isinstance(result, AppendResult)
    assert result.added == 1
    assert result.first_number == 2

    after_r = readme.read_text(encoding="utf-8")
    after_i = instances.read_text(encoding="utf-8")
    assert after_r.startswith(before_r)
    assert after_i.startswith(before_i)
    assert "| 2 |" in after_r
    assert "**Beta Channel**" in after_r
    assert "2. Beta Channel" in after_i
    assert "https://example.com/beta" in after_i
    assert "archive: https://web.archive.org/web/9/" in after_i


def test_append_empty_is_noop(tmp_path: Path):
    readme = tmp_path / "README.md"
    instances = tmp_path / "instances.txt"
    readme.write_text(README_SEED, encoding="utf-8")
    instances.write_text(INSTANCES_SEED, encoding="utf-8")
    before_r = readme.read_bytes()
    before_i = instances.read_bytes()
    result = append_candidates(readme, instances, [])
    assert result.added == 0
    assert readme.read_bytes() == before_r
    assert instances.read_bytes() == before_i


def test_append_requires_archive_for_each_source(tmp_path: Path):
    readme = tmp_path / "README.md"
    instances = tmp_path / "instances.txt"
    readme.write_text(README_SEED, encoding="utf-8")
    instances.write_text(INSTANCES_SEED, encoding="utf-8")
    before_r = readme.read_text(encoding="utf-8")
    draft = _draft(archive_urls={})
    try:
        append_candidates(readme, instances, [draft])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "archive" in str(exc).lower()
    assert readme.read_text(encoding="utf-8") == before_r

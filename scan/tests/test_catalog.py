"""
Tests for parsing the plaintext catalog and duplicate detection.
"""

from pathlib import Path

from takedowns_scan.catalog import CatalogIndex, load_catalog_index


SAMPLE_INSTANCES = """\
Firearms creators punished for ordinary gun content

1. Demolition Ranch (Matt Carriker)
   Audience: ~11.8M YouTube subs
   When: Jul 2024
   Platform: YouTube
   What: age-gated
   Sources: https://example.com/a

2. Hickok45 (Greg/John Kinman)
   Audience: ~7.8M YouTube subs
   When: Jul 2024
   Platform: YouTube
   What: sponsor links
   Sources: https://example.com/b
"""


def test_load_catalog_index_extracts_names(tmp_path: Path):
    path = tmp_path / "instances.txt"
    path.write_text(SAMPLE_INSTANCES, encoding="utf-8")
    index = load_catalog_index(path)
    assert isinstance(index, CatalogIndex)
    assert index.contains_entity("Demolition Ranch")
    assert index.contains_entity("matt carriker")  # case-insensitive
    assert index.contains_entity("Hickok45")
    assert not index.contains_entity("Completely Unknown Creator XYZ")


def test_catalog_reports_known_source_urls(tmp_path: Path):
    path = tmp_path / "instances.txt"
    path.write_text(SAMPLE_INSTANCES, encoding="utf-8")
    index = load_catalog_index(path)
    assert index.contains_source("https://example.com/a")
    assert not index.contains_source("https://example.com/missing")

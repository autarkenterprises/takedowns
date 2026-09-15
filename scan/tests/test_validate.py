"""
Tests for candidate schema validation and rigor gates before queueing.
"""

from takedowns_scan.models import CandidateDraft
from takedowns_scan.validate import ValidationResult, validate_candidate


def _base(**overrides):
    data = {
        "who": "Example Firearms Channel",
        "audience": "~500K YouTube subs",
        "when": "Sep 2026",
        "platform": "YouTube",
        "what_happened": (
            "Partner Program removal for ordinary gun-review content with no "
            "manufacturing tutorials or sales of illegal items."
        ),
        "content_description": "ordinary firearm reviews",
        "sources": ["https://news.example.com/creator-demonetized"],
        "fit_rationale": "Matches ordinary lawful review content bar.",
        "confidence": 0.82,
    }
    data.update(overrides)
    return CandidateDraft(**data)


def test_valid_candidate_passes():
    result = validate_candidate(_base(), known_entities=set(), known_sources=set())
    assert isinstance(result, ValidationResult)
    assert result.accepted is True
    assert result.errors == []


def test_missing_source_rejected():
    result = validate_candidate(
        _base(sources=[]),
        known_entities=set(),
        known_sources=set(),
    )
    assert result.accepted is False
    assert "missing_citation" in result.errors


def test_non_http_source_rejected():
    result = validate_candidate(
        _base(sources=["ftp://bad.example/file"]),
        known_entities=set(),
        known_sources=set(),
    )
    assert result.accepted is False
    assert "invalid_citation_scheme" in result.errors


def test_duplicate_entity_rejected():
    result = validate_candidate(
        _base(who="Demolition Ranch"),
        known_entities={"demolition ranch"},
        known_sources=set(),
    )
    assert result.accepted is False
    assert "duplicate_entity" in result.errors


def test_exclusion_content_rejected():
    result = validate_candidate(
        _base(
            what_happened="Banned for posting a manufacturing tutorial for illegal firearms.",
            content_description="manufacturing tutorial",
        ),
        known_entities=set(),
        known_sources=set(),
    )
    assert result.accepted is False
    assert any(e.startswith("exclusion_") for e in result.errors)


def test_low_confidence_rejected():
    result = validate_candidate(
        _base(confidence=0.2),
        known_entities=set(),
        known_sources=set(),
        min_confidence=0.55,
    )
    assert result.accepted is False
    assert "low_confidence" in result.errors

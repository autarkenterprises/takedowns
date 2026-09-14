"""
Rigor gates applied after Grok proposes a candidate and before queueing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from takedowns_grokbot.catalog import normalize_entity_name, normalize_source_url
from takedowns_grokbot.criterion import evaluate_criterion_fit
from takedowns_grokbot.models import CandidateDraft


@dataclass
class ValidationResult:
    """Accepted flag plus machine-readable error codes for the UI/logs."""

    accepted: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def validate_candidate(
    draft: CandidateDraft,
    known_entities: set[str],
    known_sources: set[str],
    min_confidence: float = 0.55,
) -> ValidationResult:
    """
    Enforce catalog rigor without trusting the model.

    Checks: required fields, http(s) citations, confidence floor, criterion
    exclusions, and duplicate entity/source detection against the live catalog.
    """
    errors: list[str] = []
    notes: list[str] = []

    for field_name in ("who", "audience", "when", "platform", "what_happened"):
        if not getattr(draft, field_name, "").strip():
            errors.append(f"missing_field:{field_name}")

    if not draft.sources:
        errors.append("missing_citation")
    else:
        for src in draft.sources:
            parsed = urlparse(src)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append("invalid_citation_scheme")
                break
            if normalize_source_url(src) in known_sources:
                errors.append("duplicate_source")
                break

    if draft.confidence < min_confidence:
        errors.append("low_confidence")

    who_norm = normalize_entity_name(draft.who)
    if who_norm and who_norm in {normalize_entity_name(e) for e in known_entities}:
        errors.append("duplicate_entity")
    else:
        # Fuzzy: known_entities may already be normalized.
        for known in known_entities:
            k = normalize_entity_name(known)
            if who_norm and (who_norm in k or k in who_norm):
                errors.append("duplicate_entity")
                break

    verdict = evaluate_criterion_fit(draft.what_happened, draft.content_description)
    if not verdict.included:
        errors.append(verdict.reason_code)
        notes.append(verdict.detail)

    if not draft.fit_rationale.strip():
        notes.append("empty_fit_rationale")

    return ValidationResult(accepted=not errors, errors=errors, notes=notes)

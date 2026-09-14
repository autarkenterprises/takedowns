"""
Deterministic inclusion/exclusion criterion for catalog candidates.

The LLM may propose candidates; this module is the non-negotiable gate that
encodes the same bar used for the hand-compiled batches in README.md /
instances.txt: ordinary lawful firearms content only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# Substrings matched case-insensitively against what_happened + content_description.
# Kept intentionally narrow so ordinary "manufacturer channel banned" cases still pass.
EXCLUSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "exclusion_manufacturing": (
        "manufacturing tutorial",
        "how to manufacture",
        "how-to manufacture",
        "build an illegal",
        "ghost gun build instructions",
        "unserialized firearm manufacturing",
        "3d printed ghost gun instructions",
    ),
    "exclusion_threats": (
        "threats of violence",
        "violent threats",
        "threat to kill",
        "death threat",
        "threatening to shoot",
    ),
    "exclusion_illegal_sales": (
        "illegal firearm sales",
        "illegal firearms sales",
        "illegal gun sales",
        "facilitating illegal",
        "straw purchase",
        "unlicensed dealing",
    ),
}

# If an exclusion phrase appears after one of these, treat it as a denial
# ("no manufacturing tutorials") rather than an inclusion of banned conduct.
_NEGATION_BEFORE = re.compile(
    r"(?:\bno\b|\bnot\b|\bwithout\b|\bnor\b)[\w\s\-,'\"]{0,24}$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InclusionVerdict:
    """Result of applying the catalog criterion to free-text fields."""

    included: bool
    reason_code: str
    detail: str = ""


def _phrase_is_negated(blob: str, start: int) -> bool:
    """True when the match is in a 'no/without ...' denial clause."""
    return bool(_NEGATION_BEFORE.search(blob[:start]))


def evaluate_criterion_fit(what_happened: str, content_description: str = "") -> InclusionVerdict:
    """
    Return whether the described conduct belongs in the catalog.

    Exclusion phrases win unless clearly negated. Otherwise we treat the case
    as ordinary lawful content (the positive bar used by the manual batches).
    """
    blob = f"{what_happened}\n{content_description}".lower()
    for reason_code, phrases in EXCLUSION_KEYWORDS.items():
        for phrase in phrases:
            start = 0
            while True:
                idx = blob.find(phrase, start)
                if idx < 0:
                    break
                if not _phrase_is_negated(blob, idx):
                    return InclusionVerdict(
                        included=False,
                        reason_code=reason_code,
                        detail=f"matched exclusion phrase: {phrase!r}",
                    )
                start = idx + len(phrase)
    return InclusionVerdict(
        included=True,
        reason_code="ordinary_lawful_content",
        detail="no exclusion phrases matched",
    )

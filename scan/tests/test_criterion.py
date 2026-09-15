"""
Failing-first tests for catalog scanner inclusion/exclusion criterion.

These encode the catalog bar: ordinary lawful firearms content only,
with hard exclusions for manufacturing tutorials, threats, and illegal sales.
"""

from takedowns_scan.criterion import (
    EXCLUSION_KEYWORDS,
    InclusionVerdict,
    evaluate_criterion_fit,
)


def test_review_content_is_included():
    verdict = evaluate_criterion_fit(
        what_happened=(
            "YouTube demonetized a channel for ordinary handgun review videos "
            "with no sales pitch or manufacturing instructions."
        ),
        content_description="standard firearm reviews and range demos",
    )
    assert verdict.included is True
    assert verdict.reason_code == "ordinary_lawful_content"


def test_sport_photos_are_included():
    verdict = evaluate_criterion_fit(
        what_happened="Instagram restricted an Olympic shooter's competition photos with a rifle.",
        content_description="sport competition photographs",
    )
    assert verdict.included is True


def test_manufacturing_tutorial_is_excluded():
    verdict = evaluate_criterion_fit(
        what_happened="Channel banned for a how-to video on manufacturing an unserialized firearm.",
        content_description="ghost gun manufacturing tutorial",
    )
    assert verdict.included is False
    assert verdict.reason_code == "exclusion_manufacturing"


def test_threats_are_excluded():
    verdict = evaluate_criterion_fit(
        what_happened="Account removed after posting threats of violence involving firearms.",
        content_description="violent threats",
    )
    assert verdict.included is False
    assert verdict.reason_code == "exclusion_threats"


def test_illegal_sales_are_excluded():
    verdict = evaluate_criterion_fit(
        what_happened="Page taken down for facilitating illegal firearm sales across state lines.",
        content_description="illegal sales facilitation",
    )
    assert verdict.included is False
    assert verdict.reason_code == "exclusion_illegal_sales"


def test_exclusion_keyword_table_is_nonempty():
    """Guardrail: the exclusion table must stay intentional and non-trivial."""
    assert "manufactur" in " ".join(EXCLUSION_KEYWORDS).lower() or any(
        "manufactur" in k for k in EXCLUSION_KEYWORDS
    )
    assert isinstance(InclusionVerdict(True, "ordinary_lawful_content", ""), InclusionVerdict)

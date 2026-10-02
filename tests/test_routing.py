from __future__ import annotations

from app.policy import after_draft, after_extract


def test_low_confidence_goes_to_human_review() -> None:
    state = {
        "classification_confidence": 0.55,
        "answer_confidence": 0.95,
        "category": "how_to",
        "priority": "low",
    }
    assert after_draft(state) == "human_review"


def test_security_always_goes_to_human_review() -> None:
    state = {
        "classification_confidence": 0.99,
        "answer_confidence": 0.99,
        "category": "security",
        "priority": "high",
    }
    assert after_draft(state) == "human_review"


def test_high_confidence_normal_ticket_auto_routes() -> None:
    state = {
        "classification_confidence": 0.93,
        "answer_confidence": 0.91,
        "category": "billing",
        "priority": "medium",
    }
    assert after_draft(state) == "auto_route"


def test_extract_retries_then_reviews() -> None:
    assert after_extract({"extraction_error": "bad json", "extraction_attempts": 1}) == "extract"
    assert after_extract({"extraction_error": "bad json", "extraction_attempts": 2}) == "human_review"
    assert after_extract({"extraction_error": None, "extracted": {"issue_summary": "ok"}}) == "retrieve"

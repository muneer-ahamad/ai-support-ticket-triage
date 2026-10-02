from __future__ import annotations

from app.config import settings
from app.state import TicketState


def after_extract(state: TicketState) -> str:
    if not state.get("extraction_error") and state.get("extracted"):
        return "retrieve"
    if int(state.get("extraction_attempts", 0)) < settings.max_extract_retries:
        return "extract"
    return "human_review"


def after_draft(state: TicketState) -> str:
    classification_confidence = float(state.get("classification_confidence", 0.0))
    answer_confidence = float(state.get("answer_confidence", 0.0))
    category = state.get("category")
    priority = state.get("priority")

    requires_review = (
        classification_confidence < settings.confidence_threshold
        or answer_confidence < settings.confidence_threshold
        or category == "security"
        or priority == "urgent"
    )
    return "human_review" if requires_review else "auto_route"

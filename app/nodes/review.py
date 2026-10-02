from __future__ import annotations

from langgraph.types import interrupt

from app.schemas import HumanReviewDecision, RouteTarget
from app.state import TicketState


def human_review_node(state: TicketState) -> dict:
    payload = {
        "reason": "Human approval required before final routing.",
        "subject": state.get("subject"),
        "category": state.get("category"),
        "priority": state.get("priority"),
        "classification_confidence": state.get("classification_confidence"),
        "answer_confidence": state.get("answer_confidence"),
        "extracted": state.get("extracted"),
        "draft_reply": state.get("draft_reply", ""),
        "suggested_route": state.get("route_to"),
        "errors": state.get("errors", []),
    }
    raw_decision = interrupt(payload)
    decision = HumanReviewDecision.model_validate(raw_decision)

    if not decision.approved:
        return {
            "status": "rejected_by_reviewer",
            "route_to": RouteTarget.HUMAN_REVIEW.value,
            "final_reply": decision.edited_reply or state.get("draft_reply", ""),
            "human_note": decision.note,
        }

    return {
        "status": "human_approved",
        "route_to": (decision.route_to or RouteTarget.HUMAN_REVIEW).value,
        "final_reply": decision.edited_reply or state.get("draft_reply", ""),
        "human_note": decision.note,
    }

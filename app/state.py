from __future__ import annotations

from typing import Any, TypedDict


class TicketState(TypedDict, total=False):
    thread_id: str
    subject: str
    body: str
    customer_email: str | None

    category: str
    queue: str
    ticket_type: str
    priority: str
    classification_confidence: float
    classification_rationale: str

    extracted: dict[str, Any]
    extraction_attempts: int
    extraction_error: str | None

    retrieved_docs: list[dict[str, Any]]
    draft_reply: str
    answer_confidence: float
    citations: list[str]

    route_to: str
    status: str
    final_reply: str
    human_note: str | None
    errors: list[str]

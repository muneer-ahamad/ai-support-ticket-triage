from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import Classification, Priority, TicketCategory, TicketInput


def test_ticket_input_accepts_valid_ticket() -> None:
    ticket = TicketInput(
        subject="Cannot log in",
        body="My authenticator codes are rejected and I cannot access my account.",
        customer_email="user@example.com",
    )
    assert ticket.customer_email == "user@example.com"


def test_ticket_input_rejects_too_short_body() -> None:
    with pytest.raises(ValidationError):
        TicketInput(subject="Login issue", body="too short")


def test_classification_confidence_must_be_probability() -> None:
    with pytest.raises(ValidationError):
        Classification(
            category=TicketCategory.BUG,
            priority=Priority.MEDIUM,
            confidence=1.2,
            rationale="Clearly a product bug.",
        )

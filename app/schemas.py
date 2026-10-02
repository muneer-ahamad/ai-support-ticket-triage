from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class TicketCategory(str, Enum):
    ACCOUNT_ACCESS = "account_access"
    BILLING = "billing"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    HOW_TO = "how_to"
    SECURITY = "security"
    PERFORMANCE = "performance"
    OTHER = "other"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportQueue(str, Enum):
    TECHNICAL_SUPPORT = "Technical Support"
    CUSTOMER_SERVICE = "Customer Service"
    PRODUCT_SUPPORT = "Product Support"
    BILLING_AND_PAYMENTS = "Billing and Payments"
    IT_SUPPORT = "IT Support"
    RETURNS_AND_EXCHANGES = "Returns and Exchanges"
    SERVICE_OUTAGES_AND_MAINTENANCE = "Service Outages and Maintenance"
    SALES_AND_PRE_SALES = "Sales and Pre-Sales"
    HUMAN_RESOURCES = "Human Resources"
    GENERAL_INQUIRY = "General Inquiry"


class TicketType(str, Enum):
    INCIDENT = "Incident"
    REQUEST = "Request"
    PROBLEM = "Problem"
    CHANGE = "Change"

class RouteTarget(str, Enum):
    ACCOUNT_TEAM = "account_team"
    BILLING_TEAM = "billing_team"
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SUPPORT = "support"
    SECURITY_TEAM = "security_team"
    HUMAN_REVIEW = "human_review"


class TicketInput(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10, max_length=10_000)
    customer_email: EmailStr | None = None


class Classification(BaseModel):
    category: TicketCategory
    queue: SupportQueue
    ticket_type: TicketType
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=3, max_length=600)


class ExtractedFields(BaseModel):
    issue_summary: str = Field(min_length=5, max_length=800)
    product_area: str | None = Field(default=None, max_length=120)
    account_id: str | None = Field(default=None, max_length=120)
    order_or_invoice_id: str | None = Field(default=None, max_length=120)
    error_codes: list[str] = Field(default_factory=list, max_length=10)
    requested_action: str | None = Field(default=None, max_length=500)
    urgency_signals: list[str] = Field(default_factory=list, max_length=10)
    pii_present: bool = False

    @field_validator("error_codes", "urgency_signals")
    @classmethod
    def strip_blank_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class RetrievedDocument(BaseModel):
    id: str
    title: str
    content: str
    distance: float | None = None


class DraftReply(BaseModel):
    reply: str = Field(min_length=20, max_length=4000)
    answer_confidence: float = Field(ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list)


class HumanReviewDecision(BaseModel):
    approved: bool
    edited_reply: str | None = Field(default=None, max_length=4000)
    route_to: RouteTarget | None = None
    note: str | None = Field(default=None, max_length=1000)


class TicketResult(BaseModel):
    thread_id: str
    status: str
    category: TicketCategory | None = None
    queue: SupportQueue | None = None
    ticket_type: TicketType | None = None
    priority: Priority | None = None
    classification_confidence: float | None = None
    extracted: ExtractedFields | None = None
    retrieved_docs: list[RetrievedDocument] = Field(default_factory=list)
    draft_reply: str | None = None
    final_reply: str | None = None
    route_to: RouteTarget | None = None
    human_review_payload: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    model: str
    embedding_model: str

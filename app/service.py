from __future__ import annotations

from functools import lru_cache
from uuid import uuid4

from langgraph.types import Command

from app.graph import build_graph
from app.nodes.route import CATEGORY_ROUTES
from app.schemas import HumanReviewDecision, RetrievedDocument, RouteTarget, TicketInput, TicketResult


class TriageService:
    def __init__(self) -> None:
        self.graph = build_graph()

    @staticmethod
    def _interrupt_payload(result: dict) -> dict | None:
        interrupts = result.get("__interrupt__") or []
        if not interrupts:
            return None
        interrupt_obj = interrupts[0]
        return getattr(interrupt_obj, "value", interrupt_obj)

    @staticmethod
    def _to_result(thread_id: str, state: dict) -> TicketResult:
        payload = TriageService._interrupt_payload(state)
        docs = [RetrievedDocument.model_validate(item) for item in (state.get("retrieved_docs") or [])]
        route_raw = state.get("route_to")
        route = RouteTarget(route_raw) if route_raw in {item.value for item in RouteTarget} else None

        status = state.get("status") or ("review_required" if payload else "processing")
        if payload and not payload.get("suggested_route"):
            payload["suggested_route"] = CATEGORY_ROUTES.get(state.get("category", "other"), "support")

        return TicketResult(
            thread_id=thread_id,
            status=status,
            category=state.get("category"),
	    queue=state.get("queue"),
	    ticket_type=state.get("ticket_type"),
	    priority=state.get("priority"),
            classification_confidence=state.get("classification_confidence"),
            extracted=state.get("extracted"),
            retrieved_docs=docs,
            draft_reply=state.get("draft_reply"),
            final_reply=state.get("final_reply"),
            route_to=route,
            human_review_payload=payload,
            errors=state.get("errors") or [],
        )

    def triage(self, ticket: TicketInput, thread_id: str | None = None) -> TicketResult:
        thread_id = thread_id or str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "thread_id": thread_id,
            "subject": ticket.subject,
            "body": ticket.body,
            "customer_email": str(ticket.customer_email) if ticket.customer_email else None,
            "extraction_attempts": 0,
            "errors": [],
        }
        result = self.graph.invoke(initial_state, config=config)
        return self._to_result(thread_id, result)

    def review(self, thread_id: str, decision: HumanReviewDecision) -> TicketResult:
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(Command(resume=decision.model_dump(mode="json")), config=config)
        return self._to_result(thread_id, result)


@lru_cache(maxsize=1)
def get_service() -> TriageService:
    return TriageService()

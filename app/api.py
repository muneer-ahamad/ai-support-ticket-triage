from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from app.config import settings
from app.schemas import HealthResponse, HumanReviewDecision, TicketInput, TicketResult
from app.service import TriageService, get_service

app = FastAPI(
    title="AI Support Ticket Triage API",
    version="1.0.0",
    description="LangGraph + Gemini support-ticket triage, RAG, and human review.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(model=settings.gemini_model, embedding_model=settings.embedding_model)


@app.post("/triage", response_model=TicketResult)
def triage(ticket: TicketInput, service: TriageService = Depends(get_service)) -> TicketResult:
    try:
        return service.triage(ticket)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/review/{thread_id}", response_model=TicketResult)
def review(
    thread_id: str,
    decision: HumanReviewDecision,
    service: TriageService = Depends(get_service),
) -> TicketResult:
    try:
        return service.review(thread_id, decision)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

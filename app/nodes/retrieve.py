from __future__ import annotations

from app.retriever import KnowledgeBase
from app.state import TicketState


def retrieve_node(state: TicketState, kb: KnowledgeBase) -> dict:
    extracted = state.get("extracted") or {}
    query = " | ".join(
        value
        for value in [
            state.get("subject", ""),
            extracted.get("issue_summary", ""),
            f"category: {state.get('category', '')}",
            f"product area: {extracted.get('product_area', '')}",
        ]
        if value
    )
    docs = kb.search(query)
    return {"retrieved_docs": [doc.model_dump(mode="json") for doc in docs]}

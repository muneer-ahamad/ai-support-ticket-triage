from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    if "LANGFUSE_PUBLIC_KEY" in st.secrets:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", st.secrets["LANGFUSE_PUBLIC_KEY"])
    if "LANGFUSE_SECRET_KEY" in st.secrets:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", st.secrets["LANGFUSE_SECRET_KEY"])
    if "LANGFUSE_BASE_URL" in st.secrets:
        os.environ.setdefault("LANGFUSE_BASE_URL", st.secrets["LANGFUSE_BASE_URL"])
except Exception:
    pass

from app.config import settings  # noqa: E402
from app.schemas import HumanReviewDecision, RouteTarget, TicketInput  # noqa: E402
from app.service import get_service  # noqa: E402

st.set_page_config(page_title="AI Ticket Triage", page_icon="🎫", layout="wide")


@st.cache_resource
def service():
    return get_service()


def confidence_label(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0%}"


def render_result(result) -> None:
    c1, c2, c3 = st.columns(3)

    c1.metric(
    "Category",
    result.category.value if result.category else "—",
    )

    c2.metric(
        "Queue",
        result.queue.value if result.queue else "—",
    )

    c3.metric(
        "Ticket type",
        result.ticket_type.value if result.ticket_type else "—",
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Priority",
        result.priority.value if result.priority else "—",
    )

    c5.metric(
        "Classify confidence",
        confidence_label(result.classification_confidence),
    )

    c6.metric(
        "Status",
        result.status.replace("_", " ").title(),
    ) 

    if result.extracted:
        with st.expander("Extracted fields", expanded=True):
            st.json(result.extracted.model_dump(mode="json"))

    if result.retrieved_docs:
        with st.expander("Retrieved knowledge-base context"):
            for doc in result.retrieved_docs:
                st.markdown(f"**{doc.title}**")
                st.caption(f"Vector distance: {doc.distance:.4f}" if doc.distance is not None else "")
                st.write(doc.content)

    if result.draft_reply:
        st.subheader("Draft reply")
        st.write(result.draft_reply)

    if result.final_reply:
        st.subheader("Final reply")
        st.success(result.final_reply)
        if result.route_to:
            st.info(f"Routed to: {result.route_to.value}")

    if result.errors:
        with st.expander("Workflow errors"):
            for error in result.errors:
                st.error(error)


st.title("🎫 AI Support Ticket Triage")
st.caption("Gemini + LangGraph + Pydantic + Chroma RAG + human-in-the-loop")

if not settings.gemini_api_key:
    st.error("GEMINI_API_KEY is not configured. Add it to .env locally or Streamlit Secrets in deployment.")
    st.stop()

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"**LLM:** `{settings.gemini_model}`")
    st.write(f"**Embeddings:** `{settings.embedding_model}`")
    st.write(f"**Review threshold:** `{settings.confidence_threshold:.0%}`")
    st.caption("Security and urgent tickets always require human review.")

subject = st.text_input("Ticket subject", value="Can't sign in after enabling MFA")
body = st.text_area(
    "Ticket body",
    value=(
        "I enabled MFA yesterday and now every code from my authenticator is rejected. "
        "I need access before a customer demo this afternoon. My account email is alex@example.com."
    ),
    height=170,
)
email = st.text_input("Customer email (optional)", value="alex@example.com")

if st.button("Run triage", type="primary", use_container_width=True):
    try:
        with st.spinner("Running LangGraph workflow..."):
            result = service().triage(
                TicketInput(subject=subject, body=body, customer_email=email or None)
            )
        st.session_state["last_result"] = result
    except Exception as exc:
        st.exception(exc)

result = st.session_state.get("last_result")
if result:
    st.divider()
    render_result(result)

    if result.status == "review_required" and result.human_review_payload:
        st.subheader("Human review required")
        payload = result.human_review_payload
        st.warning(payload.get("reason", "Review required."))

        edited = st.text_area(
            "Edit reply before approval",
            value=payload.get("draft_reply") or "",
            height=190,
            key=f"edited-{result.thread_id}",
        )
        suggested = payload.get("suggested_route") or RouteTarget.HUMAN_REVIEW.value
        route_values = [item.value for item in RouteTarget if item != RouteTarget.HUMAN_REVIEW]
        default_index = route_values.index(suggested) if suggested in route_values else 0
        route = st.selectbox("Route to", route_values, index=default_index)
        note = st.text_input("Reviewer note (optional)")

        approve_col, reject_col = st.columns(2)
        if approve_col.button("Approve and route", type="primary", use_container_width=True):
            reviewed = service().review(
                result.thread_id,
                HumanReviewDecision(
                    approved=True,
                    edited_reply=edited or None,
                    route_to=RouteTarget(route),
                    note=note or None,
                ),
            )
            st.session_state["last_result"] = reviewed
            st.rerun()

        if reject_col.button("Reject", use_container_width=True):
            reviewed = service().review(
                result.thread_id,
                HumanReviewDecision(
                    approved=False,
                    edited_reply=edited or None,
                    route_to=RouteTarget.HUMAN_REVIEW,
                    note=note or "Reviewer rejected automatic handling.",
                ),
            )
            st.session_state["last_result"] = reviewed
            st.rerun()

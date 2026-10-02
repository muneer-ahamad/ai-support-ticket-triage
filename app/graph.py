from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from app.llm import GeminiClient
from app.nodes.classify import classify_node
from app.nodes.draft import draft_node
from app.nodes.extract import extract_node
from app.nodes.retrieve import retrieve_node
from app.nodes.review import human_review_node
from app.nodes.route import auto_route_node
from app.retriever import KnowledgeBase
from app.state import TicketState
from app.policy import after_draft, after_extract


def build_graph():
    llm = GeminiClient()
    kb = KnowledgeBase(llm)

    builder = StateGraph(TicketState)
    builder.add_node("classify", lambda state: classify_node(state, llm))
    builder.add_node("extract", lambda state: extract_node(state, llm))
    builder.add_node("retrieve", lambda state: retrieve_node(state, kb))
    builder.add_node("draft", lambda state: draft_node(state, llm))
    builder.add_node("human_review", human_review_node)
    builder.add_node("auto_route", auto_route_node)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "extract")
    builder.add_conditional_edges(
        "extract",
        after_extract,
        {"extract": "extract", "retrieve": "retrieve", "human_review": "human_review"},
    )
    builder.add_edge("retrieve", "draft")
    builder.add_conditional_edges(
        "draft",
        after_draft,
        {"human_review": "human_review", "auto_route": "auto_route"},
    )
    builder.add_edge("human_review", END)
    builder.add_edge("auto_route", END)

    checkpoint_path = Path(settings.checkpoint_db)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()

    return builder.compile(checkpointer=checkpointer)

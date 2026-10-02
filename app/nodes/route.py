from __future__ import annotations

from app.schemas import RouteTarget
from app.state import TicketState


CATEGORY_ROUTES = {
    "account_access": RouteTarget.ACCOUNT_TEAM.value,
    "billing": RouteTarget.BILLING_TEAM.value,
    "bug": RouteTarget.ENGINEERING.value,
    "feature_request": RouteTarget.PRODUCT.value,
    "how_to": RouteTarget.SUPPORT.value,
    "security": RouteTarget.SECURITY_TEAM.value,
    "performance": RouteTarget.ENGINEERING.value,
    "other": RouteTarget.SUPPORT.value,
}


def auto_route_node(state: TicketState) -> dict:
    route_to = CATEGORY_ROUTES.get(state.get("category", "other"), RouteTarget.SUPPORT.value)
    return {
        "route_to": route_to,
        "final_reply": state.get("draft_reply", ""),
        "status": "auto_routed",
    }

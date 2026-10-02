from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import settings


def langfuse_enabled() -> bool:
    required = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
    return settings.enable_langfuse and all(os.getenv(key) for key in required)


@contextmanager
def trace_span(name: str, *, as_type: str = "span", **kwargs: Any) -> Iterator[Any]:
    """Use Langfuse when configured, otherwise behave as a no-op context manager."""
    if not langfuse_enabled():
        yield None
        return

    try:
        from langfuse import get_client
        client = get_client()
        observation_cm = client.start_as_current_observation(as_type=as_type, name=name, **kwargs)
    except Exception:
        yield None
        return

    with observation_cm as span:
        yield span

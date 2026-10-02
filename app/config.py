from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    chroma_dir: str = os.getenv("CHROMA_DIR", str(BASE_DIR / ".chroma"))
    checkpoint_db: str = os.getenv("CHECKPOINT_DB", str(BASE_DIR / ".langgraph_checkpoints.sqlite"))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.78"))
    max_extract_retries: int = int(os.getenv("MAX_EXTRACT_RETRIES", "2"))
    kb_top_k: int = int(os.getenv("KB_TOP_K", "3"))
    enable_langfuse: bool = os.getenv("ENABLE_LANGFUSE", "false").lower() in {"1", "true", "yes"}
    langfuse_capture_content: bool = os.getenv("LANGFUSE_CAPTURE_CONTENT", "false").lower() in {"1", "true", "yes"}

    @property
    def kb_dir(self) -> Path:
        return BASE_DIR / "app" / "kb"


settings = Settings()

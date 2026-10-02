from __future__ import annotations

from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.tracing import trace_span

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Copy .env.example to .env and add your Gemini API key."
            )
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def structured(self, prompt: str, schema: type[T], *, temperature: float = 0.1) -> T:
        trace_kwargs = {"model": settings.gemini_model}
        if settings.langfuse_capture_content:
            trace_kwargs["input"] = prompt
        with trace_span(
            "gemini-structured-output",
            as_type="generation",
            **trace_kwargs,
        ) as span:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            result = response.parsed if isinstance(response.parsed, schema) else schema.model_validate_json(response.text)
            if span is not None and settings.langfuse_capture_content:
                span.update(output=result.model_dump(mode="json"))
            return result

    def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> list[list[float]]:
        embeddings: list[list[float]] = []
        titles = titles or [""] * len(texts)
        for text, title in zip(texts, titles, strict=True):
            response = self.client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    title=title or None,
                    output_dimensionality=768,
                ),
            )
            embeddings.append(list(response.embeddings[0].values))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768,
            ),
        )
        return list(response.embeddings[0].values)

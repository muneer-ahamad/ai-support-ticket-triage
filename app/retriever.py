from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb

from app.config import settings
from app.llm import GeminiClient
from app.schemas import RetrievedDocument


class KnowledgeBase:
    def __init__(self, llm: GeminiClient) -> None:
        self.llm = llm
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _doc_id(path: Path, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        return f"{path.stem}-{digest}"

    def ensure_indexed(self) -> int:
        paths = sorted(settings.kb_dir.glob("*.md"))
        if not paths:
            raise RuntimeError(f"No knowledge-base documents found in {settings.kb_dir}")

        ids: list[str] = []
        docs: list[str] = []
        titles: list[str] = []
        metadatas: list[dict[str, str]] = []

        for path in paths:
            text = path.read_text(encoding="utf-8").strip()
            title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
            ids.append(self._doc_id(path, text))
            docs.append(text)
            titles.append(title)
            metadatas.append({"title": title, "source": path.name})

        existing = self.collection.get(ids=ids)
        existing_ids = set(existing.get("ids", []))
        missing = [i for i, doc_id in enumerate(ids) if doc_id not in existing_ids]
        if not missing:
            return 0

        missing_docs = [docs[i] for i in missing]
        missing_titles = [titles[i] for i in missing]
        embeddings = self.llm.embed_documents(missing_docs, missing_titles)
        self.collection.upsert(
            ids=[ids[i] for i in missing],
            documents=missing_docs,
            embeddings=embeddings,
            metadatas=[metadatas[i] for i in missing],
        )
        return len(missing)

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        self.ensure_indexed()
        query_embedding = self.llm.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k or settings.kb_top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]

        output: list[RetrievedDocument] = []
        for doc_id, content, metadata, distance in zip(ids, documents, metadatas, distances, strict=False):
            output.append(
                RetrievedDocument(
                    id=str(doc_id),
                    title=str((metadata or {}).get("title", "Knowledge base article")),
                    content=str(content),
                    distance=float(distance) if distance is not None else None,
                )
            )
        return output

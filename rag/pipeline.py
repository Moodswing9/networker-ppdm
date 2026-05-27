"""RAG pipeline: build index from SKILL.md, retrieve, answer."""

from __future__ import annotations

from pathlib import Path

import anthropic

from rag.chunker import load_chunks
from rag.embedder import embed
from rag.retriever import VectorStore

_LLM_MODEL = "claude-opus-4-7"
_CACHE_FILE = ".rag_index.json"


class RagPipeline:
    def __init__(self, skill_path: str = "SKILL.md") -> None:
        self._skill_path = skill_path
        self._store = VectorStore()

    def build_index(self, force: bool = False) -> None:
        """Build or load the vector index from SKILL.md."""
        cache = Path(_CACHE_FILE)
        if cache.exists() and not force:
            skill = Path(self._skill_path)
            cache_is_stale = skill.exists() and skill.stat().st_mtime > cache.stat().st_mtime
            if not cache_is_stale:
                self._store.load(cache)
                return

        chunks = load_chunks(self._skill_path)
        texts = [f"{c['heading']}\n{c['text']}" for c in chunks]
        vectors = embed(texts)
        self._store.add(chunks, vectors)
        self._store.save(cache)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        if len(self._store) == 0:
            self.build_index()
        [query_vec] = embed([query])
        return self._store.query(query_vec, top_k=top_k)

    def ask(self, question: str, top_k: int = 5) -> str:
        """Answer a question using retrieved context + Claude Opus 4.7."""
        hits = self.retrieve(question, top_k=top_k)
        context = "\n\n---\n\n".join(
            f"[{h['heading']}]\n{h['text']}" for h in hits
        )

        client = anthropic.Anthropic()

        system_prompt = (
            "You are an expert Dell EMC NetWorker and PPDM administrator. "
            "Use the provided context to give accurate, concise answers. "
            "If the answer is not in the context, say so clearly."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

        msg = client.messages.create(
            model=_LLM_MODEL,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return next((b.text for b in msg.content if b.type == "text"), "")

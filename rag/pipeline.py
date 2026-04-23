"""RAG pipeline: build index from SKILL.md, retrieve, answer."""

from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

from rag.chunker import load_chunks
from rag.embedder import embed
from rag.retriever import VectorStore

_LLM_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
_CACHE_FILE = ".rag_index.json"


class RagPipeline:
    def __init__(self, skill_path: str = "SKILL.md") -> None:
        self._skill_path = skill_path
        self._store = VectorStore()

    def build_index(self, force: bool = False) -> None:
        """Build or load the vector index from SKILL.md."""
        cache = Path(_CACHE_FILE)
        if cache.exists() and not force:
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
        """Answer a question using retrieved context + Nemotron 70B."""
        hits = self.retrieve(question, top_k=top_k)
        context = "\n\n---\n\n".join(
            f"[{h['heading']}]\n{h['text']}" for h in hits
        )

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ["NVIDIA_API_KEY"],
        )

        system_prompt = (
            "You are an expert Dell EMC NetWorker and PPDM administrator. "
            "Use the provided context to give accurate, concise answers. "
            "If the answer is not in the context, say so clearly."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

        resp = client.chat.completions.create(
            model=_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        return resp.choices[0].message.content or ""

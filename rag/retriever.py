"""In-memory vector store with cosine similarity retrieval."""

from __future__ import annotations

import json
import math
from pathlib import Path


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


class VectorStore:
    def __init__(self) -> None:
        self._chunks: list[dict] = []      # {heading, text}
        self._vectors: list[list[float]] = []

    def add(self, chunks: list[dict], vectors: list[list[float]]) -> None:
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)

    def query(self, query_vec: list[float], top_k: int = 5) -> list[dict]:
        scored = [
            (i, _cosine(query_vec, v)) for i, v in enumerate(self._vectors)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {**self._chunks[i], "score": score}
            for i, score in scored[:top_k]
        ]

    def save(self, path: str | Path) -> None:
        data = {"chunks": self._chunks, "vectors": self._vectors}
        Path(path).write_text(json.dumps(data), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._chunks = data["chunks"]
        self._vectors = data["vectors"]

    def __len__(self) -> int:
        return len(self._chunks)

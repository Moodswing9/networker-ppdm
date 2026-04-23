"""Embed text using NVIDIA NIM NemoRetriever model."""

from __future__ import annotations

import os

from openai import OpenAI

_MODEL = "nvidia/llama-3.2-nemoretriever-300m-embed-v1"
_BATCH = 32


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ["NVIDIA_API_KEY"],
    )


def embed(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a list of strings, batched to avoid rate limits."""
    client = _client()
    all_vecs: list[list[float]] = []

    for i in range(0, len(texts), _BATCH):
        batch = texts[i : i + _BATCH]
        resp = client.embeddings.create(model=_MODEL, input=batch)
        resp.data.sort(key=lambda e: e.index)
        all_vecs.extend([e.embedding for e in resp.data])

    return all_vecs

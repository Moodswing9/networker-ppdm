"""RAG pipeline powered by NVIDIA NIM models."""

__all__ = ["RagPipeline"]


def __getattr__(name: str):
    # Lazy, so importing rag.chunker (the CLI does) does not require the
    # optional anthropic package that rag.pipeline imports.
    if name == "RagPipeline":
        from rag.pipeline import RagPipeline

        return RagPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

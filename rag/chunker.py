"""Split SKILL.md into retrievable chunks by heading."""

from __future__ import annotations

import re
from pathlib import Path


def load_chunks(skill_path: str | Path = "SKILL.md", max_chars: int = 800) -> list[dict]:
    """Return list of {heading, text} dicts from a Markdown file.

    Splits on level-2 headings (##). Chunks exceeding max_chars are split
    further at paragraph boundaries so embeddings stay accurate.
    """
    text = Path(skill_path).read_text(encoding="utf-8")
    sections = re.split(r"(?m)^##\s+", text)

    chunks: list[dict] = []
    for section in sections:
        if not section.strip():
            continue
        lines = section.splitlines()
        heading = lines[0].strip() if lines else "Preamble"
        body = "\n".join(lines[1:]).strip()

        if len(body) <= max_chars:
            chunks.append({"heading": heading, "text": body})
        else:
            # split at blank lines (paragraph boundaries)
            paragraphs = re.split(r"\n{2,}", body)
            current = ""
            for para in paragraphs:
                if len(current) + len(para) + 2 > max_chars and current:
                    chunks.append({"heading": heading, "text": current.strip()})
                    current = para
                else:
                    current = f"{current}\n\n{para}" if current else para
            if current.strip():
                chunks.append({"heading": heading, "text": current.strip()})

    return chunks

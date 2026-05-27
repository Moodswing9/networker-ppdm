"""Generate automation scripts using Claude Opus 4.7."""

from __future__ import annotations

import anthropic

_MODEL = "claude-opus-4-7"

_SYSTEM_PROMPT = (
    "You are an expert Dell EMC NetWorker and PowerProtect Data Manager (PPDM) "
    "automation engineer. Generate clean, production-ready Python or bash scripts "
    "that interact with the NetWorker REST API or PPDM REST API. "
    "Include error handling, logging, and comments only where the logic is non-obvious. "
    "Return only the script — no markdown fences, no prose."
)


def generate_script(description: str) -> str:
    """Return a Python or bash script matching the given description.

    Uses Claude Opus 4.7 with adaptive thinking for accurate data-protection
    domain code generation. Set ANTHROPIC_API_KEY in your environment.
    """
    client = anthropic.Anthropic()

    msg = client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": description}],
    )
    return next((b.text for b in msg.content if b.type == "text"), "")

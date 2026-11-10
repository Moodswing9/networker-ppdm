"""Generate automation scripts using Claude Opus 5.5."""

from __future__ import annotations

import anthropic

from orchestrator.claude_models import OPUS, OPUS_FALLBACK, text_of

_SYSTEM_PROMPT = (
    "You are an expert Dell EMC NetWorker and PowerProtect Data Manager (PPDM) "
    "automation engineer. Generate clean, production-ready Python or bash scripts "
    "that interact with the NetWorker REST API or PPDM REST API. "
    "Include error handling, logging, and comments only where the logic is non-obvious. "
    "Return only the script — no markdown fences, no prose."
)


def generate_script(description: str) -> str:
    """Return a Python or bash script matching the given description.

    Uses Claude Opus 5.5 with adaptive thinking at high effort for accurate data-protection
    domain code generation. Set ANTHROPIC_API_KEY in your environment.
    """
    client = anthropic.Anthropic()

    msg = client.beta.messages.create(
        model=OPUS,
        max_tokens=16000,  # thinking and the script share it
        output_config={"effort": "high"},
        **OPUS_FALLBACK,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": description}],
    )
    return text_of(msg)

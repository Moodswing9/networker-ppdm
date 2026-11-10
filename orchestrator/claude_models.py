"""Claude model settings shared by every AI feature (no anthropic import here).

Claude Opus 5.5 and Claude Haiku 5.5 always think on adaptive settings, and
thinking tokens are billed and share ``max_tokens`` with the answer. Effort sets
how much they think, so every call states it:

- calls that already used adaptive thinking on Opus 4.7 keep ``high`` (their
  effective level before), now at Opus 5.5's lower per-token price;
- calls that did not think keep cost and latency flat with ``low``, or, on
  Haiku 5.5, by turning thinking off (allowed there at ``high`` or below).
"""

from __future__ import annotations

from typing import Any

OPUS = "claude-opus-5-5"
HAIKU = "claude-haiku-5-5"

# On a policy decline, the API re-runs an Opus request on a fallback model
# (Messages API only: not Message Batches, and Haiku has no fallback).
OPUS_FALLBACK: dict[str, Any] = {
    "betas": ["server-side-fallback-2026-07-01"],
    "fallbacks": "default",
}

HAIKU_NO_THINKING: dict[str, Any] = {
    "thinking": {"type": "disabled"},
    "output_config": {"effort": "low"},
}


class ClaudeRefusal(RuntimeError):
    """Claude (and any fallback model) declined the request."""


def text_of(message: Any) -> str:
    """The reply text: every text block, skipping thinking and fallback blocks.

    Raises ClaudeRefusal when the response stopped on a refusal.
    """
    if getattr(message, "stop_reason", None) == "refusal":
        details = getattr(message, "stop_details", None)
        category = getattr(details, "category", None)
        raise ClaudeRefusal(f"Claude declined the request (category: {category or 'unspecified'}).")
    return "".join(b.text for b in message.content if b.type == "text")

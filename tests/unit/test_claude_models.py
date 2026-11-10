"""Shared Claude settings: model IDs, effort, refusal handling, reply text."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from orchestrator import claude_models as cm


def _msg(*blocks, stop_reason="end_turn", category=None):
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=category) if stop_reason == "refusal" else None,
        content=[SimpleNamespace(**b) for b in blocks],
    )


def test_current_model_ids():
    assert cm.OPUS == "claude-opus-5-5"
    assert cm.HAIKU == "claude-haiku-5-5"


def test_opus_fallback_needs_its_beta():
    assert cm.OPUS_FALLBACK["fallbacks"] == "default"
    assert cm.OPUS_FALLBACK["betas"] == ["server-side-fallback-2026-07-01"]


def test_haiku_thinking_off_stays_at_an_allowed_effort():
    # Haiku 5.5 accepts disabled thinking only at effort high or below.
    assert cm.HAIKU_NO_THINKING["thinking"] == {"type": "disabled"}
    assert cm.HAIKU_NO_THINKING["output_config"]["effort"] in {"low", "medium", "high"}


def test_text_of_skips_thinking_and_fallback_blocks():
    msg = _msg(
        {"type": "thinking", "thinking": ""},
        {"type": "text", "text": "Root cause: "},
        {"type": "fallback"},
        {"type": "text", "text": "expired vCenter credential."},
    )
    assert cm.text_of(msg) == "Root cause: expired vCenter credential."


def test_text_of_raises_on_refusal():
    with pytest.raises(cm.ClaudeRefusal, match="cyber"):
        cm.text_of(_msg(stop_reason="refusal", category="cyber"))


@pytest.mark.parametrize(
    "module",
    ["orchestrator.generate", "rag.pipeline", "scripts.dr_orchestrate", "scripts.anomaly_report", "scripts.dr_plan"],
)
def test_no_retired_model_ids_in_callers(module):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.find_spec(module)
    source = Path(spec.origin).read_text(encoding="utf-8")
    assert "claude-opus-4-7" not in source
    assert "claude-haiku-4-5" not in source

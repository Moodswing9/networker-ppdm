"""dr_plan request shape — Opus 4.7 rejects budget_tokens thinking with a 400.

A stub `anthropic` module stands in for the SDK, so these tests run in CI
without the optional AI dependency and without network access.
"""

from __future__ import annotations

import importlib
import sys
import types
from types import SimpleNamespace

import pytest


@pytest.fixture
def dr_plan(monkeypatch, tmp_path):
    calls: list[dict] = []

    class _Messages:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(type="thinking", thinking="Tier assets by criticality."),
                    SimpleNamespace(type="text", text="## DR Readiness: AT RISK"),
                ],
            )

    stub = types.ModuleType("anthropic")
    stub.Anthropic = lambda *a, **k: SimpleNamespace(messages=_Messages())
    monkeypatch.setitem(sys.modules, "anthropic", stub)
    sys.modules.pop("scripts.dr_plan", None)
    module = importlib.import_module("scripts.dr_plan")
    monkeypatch.setattr(module, "_topology", lambda: {"assets": [], "policies": [], "recent_failures": []})
    monkeypatch.chdir(tmp_path)
    yield module, calls, tmp_path
    sys.modules.pop("scripts.dr_plan", None)


def test_uses_adaptive_thinking_not_budget_tokens(dr_plan):
    module, calls, _ = dr_plan
    module.run()
    (kwargs,) = calls
    assert kwargs["thinking"]["type"] == "adaptive"
    assert "budget_tokens" not in kwargs["thinking"]
    assert kwargs["output_config"] == {"effort": "high"}


def test_requests_summarized_thinking_for_the_audit_sidecar(dr_plan):
    module, calls, tmp_path = dr_plan
    result = module.run()
    assert calls[0]["thinking"]["display"] == "summarized"
    sidecar = (tmp_path / "dr_plan_thinking.md").read_text(encoding="utf-8")
    assert "Tier assets by criticality." in sidecar
    assert result["plan"] == "## DR Readiness: AT RISK"

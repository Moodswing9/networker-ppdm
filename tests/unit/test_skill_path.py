"""SKILL.md lookup — the skill moved to skills/networker-ppdm/ when the repo became a plugin."""

from __future__ import annotations

import inspect
from pathlib import Path

from rag.chunker import DEFAULT_SKILL_PATH, load_chunks


def test_default_skill_path_points_at_plugin_skill():
    assert DEFAULT_SKILL_PATH.is_file()
    assert DEFAULT_SKILL_PATH.parts[-3:] == ("skills", "networker-ppdm", "SKILL.md")


def test_load_chunks_default_works_from_any_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no SKILL.md here
    chunks = load_chunks()
    assert len(chunks) > 50
    assert all(c["heading"] for c in chunks)


def test_pipeline_and_cli_default_to_plugin_skill():
    from orchestrator import cli
    from rag.pipeline import RagPipeline

    assert RagPipeline()._skill_path == DEFAULT_SKILL_PATH
    ask_default = inspect.signature(cli.ask).parameters["skill"].default.default
    assert Path(ask_default) == DEFAULT_SKILL_PATH


def test_skill_test_runner_points_at_plugin_skill():
    runner = (Path(__file__).resolve().parents[1] / "run_tests.py").read_text(encoding="utf-8")
    assert 'SKILL_FILE = ROOT / "skills" / "networker-ppdm" / "SKILL.md"' in runner

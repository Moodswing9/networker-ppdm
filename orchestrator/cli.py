"""Typer-based CLI for unified Dell data protection operations."""

from __future__ import annotations

import json
import sys

import typer
from rich import print
from rich.markdown import Markdown
from rich.table import Table

from orchestrator.doctor import run_doctor
from orchestrator.inventory import run_inventory
from orchestrator.protect import run_protect
from providers.datadomain import DataDomainProvider

app = typer.Typer(help="Unified CLI for PPDM, NetWorker, and Data Domain")


def _print_table(rows: list[dict]) -> None:
    if not rows:
        print("[yellow]No rows returned[/yellow]")
        return

    table = Table(show_header=True, header_style="bold")
    for col in rows[0].keys():
        table.add_column(col)

    for row in rows:
        table.add_row(*[str(row.get(col, "")) for col in rows[0].keys()])
    print(table)


@app.command()
def doctor(json_output: bool = typer.Option(False, "--json", help="Emit JSON")):
    """Run health checks across PPDM, NetWorker, and DD."""
    results = run_doctor()
    if json_output:
        print(json.dumps(results, indent=2, default=str))
        return
    _print_table(results)


@app.command()
def inventory(
    format: str = typer.Option("table", "--format", help="table or json"),
    networker_client: str | None = typer.Option(None, "--networker-client"),
):
    """Return a combined PPDM + NetWorker inventory report."""
    rows = run_inventory(networker_client=networker_client)
    if format == "json":
        print(json.dumps(rows, indent=2, default=str))
        return
    _print_table(rows)


@app.command()
def protect(
    provider: str = typer.Argument(..., help="ppdm or networker"),
    target: str = typer.Option(..., "--target", help="Policy name or group name"),
):
    """Trigger a PPDM policy backup or NetWorker group backup."""
    result = run_protect(provider=provider, target=target)
    print(json.dumps(result, indent=2, default=str))


dd_app = typer.Typer(help="Data Domain commands")
app.add_typer(dd_app, name="dd")


@dd_app.command("status")
def dd_status():
    """Show Data Domain status, filesystem, and system details."""
    result = DataDomainProvider().status()
    print(json.dumps(result, indent=2, default=str))


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question about NetWorker or PPDM"),
    top_k: int = typer.Option(5, "--top-k", help="Context chunks to retrieve"),
    skill: str = typer.Option("SKILL.md", "--skill", help="Path to SKILL.md"),
    rebuild: bool = typer.Option(False, "--rebuild", help="Force rebuild of vector index"),
):
    """Ask a NetWorker/PPDM question answered by RAG over SKILL.md.

    Requires NVIDIA_API_KEY to be set in the environment.
    """
    try:
        from rag.pipeline import RagPipeline
    except ImportError:
        print("[red]openai package required — run: pip install openai>=1.0[/red]")
        raise typer.Exit(1)

    import os
    if not os.environ.get("NVIDIA_API_KEY"):
        print("[red]NVIDIA_API_KEY is not set[/red]")
        raise typer.Exit(1)

    pipeline = RagPipeline(skill_path=skill)
    pipeline.build_index(force=rebuild)
    answer = pipeline.ask(question, top_k=top_k)
    print(Markdown(answer))


@app.command()
def generate(
    description: str = typer.Argument(..., help="Script description in plain English"),
    output: str | None = typer.Option(None, "--output", "-o", help="Save script to file"),
    skill: str = typer.Option("SKILL.md", "--skill", help="Path to SKILL.md (unused, for parity)"),
):
    """Generate a NetWorker/PPDM automation script using Qwen2.5-Coder-32B.

    Requires NVIDIA_API_KEY to be set in the environment.
    """
    try:
        from orchestrator.generate import generate_script
    except ImportError:
        print("[red]openai package required — run: pip install openai>=1.0[/red]")
        raise typer.Exit(1)

    import os
    if not os.environ.get("NVIDIA_API_KEY"):
        print("[red]NVIDIA_API_KEY is not set[/red]")
        raise typer.Exit(1)

    script = generate_script(description)

    if output:
        from pathlib import Path
        Path(output).write_text(script, encoding="utf-8")
        print(f"[green]Script written to {output}[/green]")
    else:
        print(Markdown(f"```python\n{script}\n```"))


if __name__ == "__main__":
    app()

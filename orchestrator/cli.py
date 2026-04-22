"""Typer-based CLI for unified Dell data protection operations."""

from __future__ import annotations

import json

import typer
from rich import print
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


if __name__ == "__main__":
    app()

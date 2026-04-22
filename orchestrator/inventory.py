"""Inventory aggregation for the unified CLI."""

from __future__ import annotations

from providers.networker import NetworkerProvider
from providers.ppdm import PPDMProvider


def run_inventory(networker_client: str | None = None) -> list[dict]:
    """Return a combined PPDM + NetWorker inventory view."""
    rows: list[dict] = []
    rows.extend(PPDMProvider().inventory())
    rows.extend(NetworkerProvider().inventory(client_name=networker_client))
    return rows

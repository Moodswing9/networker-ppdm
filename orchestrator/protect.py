"""Backup-trigger orchestration entry points."""

from __future__ import annotations

from providers.networker import NetworkerProvider
from providers.ppdm import PPDMProvider


def run_protect(provider: str, target: str) -> dict:
    """Dispatch a backup trigger to the selected provider."""
    if provider == "ppdm":
        return PPDMProvider().trigger_backup(target)
    if provider == "networker":
        return NetworkerProvider().trigger_group_backup(target)
    raise ValueError(f"Unsupported provider: {provider}")

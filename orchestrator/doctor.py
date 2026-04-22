"""Health-check entry points for the unified CLI."""

from __future__ import annotations

from providers.datadomain import DataDomainProvider
from providers.networker import NetworkerProvider
from providers.ppdm import PPDMProvider


def run_doctor() -> list[dict]:
    """Run health checks across all platforms."""
    providers = [PPDMProvider(), NetworkerProvider(), DataDomainProvider()]
    return [provider.healthcheck() for provider in providers]

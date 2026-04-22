"""Shared fixtures for unit tests."""

import pytest
import responses as resp_mock

from ppdm.client  import PPDMClient
from networker.client import NWClient
from datadomain.client import DDClient


PPDM_HOST = "ppdm.test"
NW_HOST   = "nw.test"
DD_HOST   = "dd.test"

PPDM_BASE = f"https://{PPDM_HOST}:8443/api/v2"
NW_BASE   = f"https://{NW_HOST}:9090/nwrestapi/v3/global"
DD_BASE   = f"https://{DD_HOST}:3009/rest/v1.0/dd-systems/0"

FAKE_TOKEN    = "fake-bearer-token"
FAKE_DD_TOKEN = "fake-dd-token"


@pytest.fixture
def ppdm_client():
    """Return a pre-authenticated PPDMClient with token already injected."""
    client = PPDMClient(PPDM_HOST, "admin", "pass")
    client._token = FAKE_TOKEN
    client._session.headers.update({"Authorization": f"Bearer {FAKE_TOKEN}"})
    return client


@pytest.fixture
def nw_client():
    """Return an NWClient (HTTP basic auth — no login step)."""
    return NWClient(NW_HOST, "administrator", "pass")


@pytest.fixture
def dd_client():
    """Return a pre-authenticated DDClient with token injected."""
    client = DDClient(DD_HOST, "sysadmin", "pass")
    client._token = FAKE_DD_TOKEN
    client._session.headers.update({"X-DD-AUTH-TOKEN": FAKE_DD_TOKEN})
    return client

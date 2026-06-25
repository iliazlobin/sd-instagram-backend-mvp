"""Test that the app starts and the healthz endpoint responds.

The healthz route pings the real database, so this test requires a running
Postgres with the instagram database.  In CI, this is provided by the compose
stack or a sandbox-side Postgres.

This test belongs to the white-box suite because it imports the app factory
directly — the black-box test_fr8_health.py in verify/acceptance/ covers the
same contract over HTTP against a running server.
"""

import pytest


@pytest.mark.asyncio
async def test_healthz_returns_ok(client):
    """GET /healthz returns 200 with status ok when DB is reachable."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"

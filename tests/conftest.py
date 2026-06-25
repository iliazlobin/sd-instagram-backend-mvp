"""White-box test fixtures — app lifecycle, test client, DB isolation."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from instagram.main import create_app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client bound to the app's ASGI transport."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

"""FastAPI application factory with lifespan management and health check."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from instagram.database import get_session_factory
from instagram.models import FeedEntry, Follow, Like, Post, User  # noqa: F401 — register ORM models
from instagram.routers import feed, follow, likes, posts, search, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle — no-op; DB sessions are per-request."""
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Instagram MVP",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(users.router)
    app.include_router(posts.router)
    app.include_router(follow.router)
    app.include_router(feed.router)
    app.include_router(search.router)
    app.include_router(likes.router)

    @app.get("/healthz")
    async def healthz():
        try:
            async with get_session_factory()() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "db": "disconnected"},
            )

    return app


app = create_app()

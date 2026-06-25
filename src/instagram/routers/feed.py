"""Feed endpoint — GET /feed."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.database import get_db
from instagram.services.feed_service import get_feed

router = APIRouter(prefix="/feed", tags=["feed"])


def _parse_cursor(cursor_str: str) -> datetime:
    """Parse a cursor string into a datetime. Handles Z and +00:00 formats."""
    try:
        # Replace Z with +00:00 for fromisoformat compatibility
        normalized = cursor_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid before cursor format") from None


@router.get("")
async def get_feed_endpoint(
    limit: int | None = Query(default=None, ge=1, le=100),
    before: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Get paginated feed for the authenticated user."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        user_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    before_dt = None
    if before:
        before_dt = _parse_cursor(before)

    items = await get_feed(db, user_id, limit=limit, before=before_dt)
    return items

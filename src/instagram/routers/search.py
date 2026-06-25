"""Search endpoint — GET /search?q=hashtag&type=hashtag."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.database import get_db
from instagram.schemas.post import PostResponse
from instagram.services.search_service import search_by_hashtag

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_hashtags(
    q: str = Query(..., min_length=1),
    type: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Search posts by hashtag."""
    if type != "hashtag":
        raise HTTPException(status_code=400, detail="Only type=hashtag is supported")

    posts = await search_by_hashtag(db, q, limit=limit, offset=offset)
    return [PostResponse.model_validate(p) for p in posts]

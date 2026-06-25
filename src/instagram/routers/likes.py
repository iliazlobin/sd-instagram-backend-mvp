"""Like endpoints — POST /posts/{post_id}/like, DELETE /posts/{post_id}/like."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.database import get_db
from instagram.schemas.like import LikeResponse
from instagram.services.like_service import (
    PostNotFoundError,
    like_post,
    unlike_post,
)

router = APIRouter(prefix="/posts", tags=["likes"])


@router.post("/{post_id}/like")
async def like_post_endpoint(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Like a post (idempotent). Returns 201 on first like, 200 if already liked."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        user_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    try:
        like, is_new = await like_post(db, post_id, user_id)
        status_code = 201 if is_new else 200
        content = LikeResponse.model_validate(like).model_dump(mode="json")
        return JSONResponse(status_code=status_code, content=content)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found") from None


@router.delete("/{post_id}/like")
async def unlike_post_endpoint(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Unlike a post. Returns 204 if unliked, 404 if not liked."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        user_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    try:
        was_liked = await unlike_post(db, post_id, user_id)
        if not was_liked:
            raise HTTPException(status_code=404, detail="Not liked")
        return Response(status_code=204)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found") from None

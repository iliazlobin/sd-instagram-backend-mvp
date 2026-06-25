"""Follow endpoints — POST /users/{followed_id}/follow, DELETE /users/{followed_id}/follow."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.database import get_db
from instagram.schemas.follow import FollowResponse
from instagram.services.follow_service import (
    SelfFollowError,
    UserNotFoundError,
    follow_user,
    unfollow_user,
)

router = APIRouter(prefix="/users", tags=["follow"])


@router.post("/{followed_id}/follow")
async def follow_user_endpoint(
    followed_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Follow a user (idempotent). Returns 201 on first follow, 200 if already following."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        follower_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    try:
        follow, is_new = await follow_user(db, follower_id, followed_id)
        status_code = 201 if is_new else 200
        content = FollowResponse.model_validate(follow).model_dump(mode="json")
        return JSONResponse(status_code=status_code, content=content)
    except SelfFollowError:
        raise HTTPException(status_code=422, detail="Cannot follow yourself") from None
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found") from None


@router.delete("/{followed_id}/follow")
async def unfollow_user_endpoint(
    followed_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Unfollow a user. Returns 204 if unfollowed, 404 if not following."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        follower_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    try:
        was_following = await unfollow_user(db, follower_id, followed_id)
        if not was_following:
            raise HTTPException(status_code=404, detail="Not following this user")
        return Response(status_code=204)
    except SelfFollowError:
        raise HTTPException(status_code=422, detail="Cannot unfollow yourself") from None
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found") from None

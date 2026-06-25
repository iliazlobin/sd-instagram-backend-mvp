"""User endpoints — POST /users, GET /users/{user_id}, GET /users/{user_id}/posts."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.database import get_db
from instagram.schemas.feed import UserPostsResponse
from instagram.schemas.user import CreateUserRequest, UserResponse
from instagram.services.post_service import get_user_posts
from instagram.services.user_service import (
    DuplicateUsernameError,
    create_user,
    get_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=201)
async def create_user_endpoint(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    try:
        user = await create_user(db, body.username, body.display_name)
        return UserResponse.model_validate(user)
    except DuplicateUsernameError:
        raise HTTPException(status_code=409, detail="Username already taken") from None


@router.get("/{user_id}")
async def get_user_endpoint(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get user profile."""
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/{user_id}/posts")
async def list_user_posts(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated posts for a user, newest first."""
    # Verify user exists
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    posts = await get_user_posts(db, user_id, limit=limit, offset=offset)
    return [UserPostsResponse.model_validate(p) for p in posts]

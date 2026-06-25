"""Like service — like/unlike, denormalized counter updates."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.models.like import Like
from instagram.models.post import Post


async def like_post(db: AsyncSession, post_id: UUID, user_id: UUID) -> tuple[Like, bool]:
    """Like a post. Returns (like, is_new) where is_new=True on first like.

    Raises:
        PostNotFoundError: if post doesn't exist
    """
    # Check post exists
    post_result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = post_result.scalar_one_or_none()
    if post is None:
        raise PostNotFoundError(f"Post {post_id} not found")

    # Check if already liked
    existing = await db.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == user_id,
        )
    )
    like = existing.scalar_one_or_none()

    if like is not None:
        # Already liked — idempotent
        return like, False

    # Create like
    like = Like(
        post_id=post_id,
        user_id=user_id,
    )
    db.add(like)
    await db.flush()

    # Update denormalized like_count
    await db.execute(
        update(Post).where(Post.post_id == post_id).values(like_count=Post.like_count + 1)
    )

    await db.flush()
    await db.refresh(like)
    return like, True


async def unlike_post(db: AsyncSession, post_id: UUID, user_id: UUID) -> bool:
    """Unlike a post. Returns True if unliked, False if not liked.

    Raises:
        PostNotFoundError: if post doesn't exist
    """
    # Check post exists
    post_result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = post_result.scalar_one_or_none()
    if post is None:
        raise PostNotFoundError(f"Post {post_id} not found")

    # Find the like
    result = await db.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == user_id,
        )
    )
    like = result.scalar_one_or_none()

    if like is None:
        return False  # Wasn't liked

    # Delete the like
    await db.delete(like)

    # Update denormalized like_count
    await db.execute(
        update(Post).where(Post.post_id == post_id).values(like_count=Post.like_count - 1)
    )

    await db.flush()
    return True


class PostNotFoundError(ValueError):
    """Raised when a referenced post does not exist."""

    pass

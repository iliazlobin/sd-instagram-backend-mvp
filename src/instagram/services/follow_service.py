"""Follow service — follow/unfollow, counters, backfill."""

from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.config import settings
from instagram.models.feed_entry import FeedEntry
from instagram.models.follow import Follow
from instagram.models.post import Post
from instagram.models.user import User


async def follow_user(
    db: AsyncSession, follower_id: UUID, followed_id: UUID
) -> tuple[Follow, bool]:
    """Follow a user. Returns (follow, is_new) where is_new=True on first follow.

    Raises:
        ValueError: on self-follow
        UserNotFoundError: if either user doesn't exist
    """
    if follower_id == followed_id:
        raise SelfFollowError("Cannot follow yourself")

    # Check both users exist
    follower = await db.execute(select(User).where(User.user_id == follower_id))
    if not follower.scalar_one_or_none():
        raise UserNotFoundError(f"User {follower_id} not found")

    followed = await db.execute(select(User).where(User.user_id == followed_id))
    if not followed.scalar_one_or_none():
        raise UserNotFoundError(f"User {followed_id} not found")

    # Check if already following
    existing = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.followed_id == followed_id,
        )
    )
    follow = existing.scalar_one_or_none()

    if follow is not None:
        # Already following — idempotent, return 200
        return follow, False

    # Create follow
    follow = Follow(
        follower_id=follower_id,
        followed_id=followed_id,
    )
    db.add(follow)
    await db.flush()

    # Update counters atomically
    await db.execute(
        update(User)
        .where(User.user_id == follower_id)
        .values(following_count=User.following_count + 1)
    )
    await db.execute(
        update(User)
        .where(User.user_id == followed_id)
        .values(follower_count=User.follower_count + 1)
    )

    # Backfill: insert last N posts from followed user into new follower's feed
    recent_posts = await db.execute(
        select(Post)
        .where(Post.user_id == followed_id)
        .order_by(Post.created_at.desc())
        .limit(settings.feed_backfill_count)
    )
    for post in recent_posts.scalars().all():
        # Check if entry already exists (unlikely but safe)
        existing_entry = await db.execute(
            select(FeedEntry).where(
                FeedEntry.user_id == follower_id,
                FeedEntry.post_id == post.post_id,
            )
        )
        if not existing_entry.scalar_one_or_none():
            entry = FeedEntry(
                user_id=follower_id,
                post_id=post.post_id,
                author_id=followed_id,
                created_at=post.created_at,
            )
            db.add(entry)

    await db.flush()
    await db.refresh(follow)
    return follow, True


async def unfollow_user(db: AsyncSession, follower_id: UUID, followed_id: UUID) -> bool:
    """Unfollow a user. Returns True if unfollowed, False if not following.

    Raises:
        ValueError: on self-unfollow
        UserNotFoundError: if either user doesn't exist
    """
    if follower_id == followed_id:
        raise SelfFollowError("Cannot unfollow yourself")

    # Find the follow relationship
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.followed_id == followed_id,
        )
    )
    follow = result.scalar_one_or_none()

    if follow is None:
        return False  # Wasn't following

    # Delete the follow
    await db.delete(follow)

    # Update counters atomically
    await db.execute(
        update(User)
        .where(User.user_id == follower_id)
        .values(following_count=User.following_count - 1)
    )
    await db.execute(
        update(User)
        .where(User.user_id == followed_id)
        .values(follower_count=User.follower_count - 1)
    )

    # Remove feed entries from the unfollowed user
    await db.execute(
        text("DELETE FROM feed_entries " "WHERE user_id = :uid AND author_id = :aid"),
        {"uid": follower_id, "aid": followed_id},
    )

    await db.flush()
    return True


class SelfFollowError(ValueError):
    """Raised when a user tries to follow/unfollow themselves."""

    pass


class UserNotFoundError(ValueError):
    """Raised when a referenced user does not exist."""

    pass

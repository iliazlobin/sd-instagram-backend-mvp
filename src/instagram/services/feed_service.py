"""Feed service — read user's feed from feed_entries table."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.config import settings
from instagram.models.feed_entry import FeedEntry
from instagram.models.post import Post
from instagram.models.user import User


def _format_dt(dt_value):
    """Format datetime as ISO 8601 with Z suffix (URL-safe, no +00:00)."""
    if isinstance(dt_value, datetime):
        if dt_value.tzinfo is None:
            dt_value = dt_value.replace(tzinfo=UTC)
        return dt_value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt_value.microsecond:06d}" + "Z"
    return str(dt_value)


async def get_feed(
    db: AsyncSession,
    user_id: UUID,
    limit: int | None = None,
    before: datetime | None = None,
) -> list[dict]:
    """Get a user's feed — posts from followed users, newest first.

    Returns list of dicts with post data + author info nested.
    """
    if limit is None:
        limit = settings.feed_default_limit
    limit = min(limit, settings.feed_max_limit)

    query = (
        select(FeedEntry, Post, User)
        .join(Post, FeedEntry.post_id == Post.post_id)
        .join(User, FeedEntry.author_id == User.user_id)
        .where(FeedEntry.user_id == user_id)
    )

    if before is not None:
        query = query.where(FeedEntry.created_at < before)

    query = query.order_by(FeedEntry.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    feed_items = []
    for feed_entry, post, author in rows:
        feed_items.append(
            {
                "post_id": str(post.post_id),
                "user_id": str(post.user_id),
                "caption": post.caption,
                "media_url": post.media_url,
                "media_type": post.media_type,
                "hashtags": post.hashtags,
                "like_count": post.like_count,
                "created_at": _format_dt(feed_entry.created_at),
                "author": {
                    "user_id": str(author.user_id),
                    "username": author.username,
                    "display_name": author.display_name,
                },
            }
        )
    return feed_items

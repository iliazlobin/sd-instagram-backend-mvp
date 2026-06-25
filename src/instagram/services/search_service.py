"""Search service — hashtag search via PostgreSQL GIN index."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.config import settings
from instagram.models.post import Post


async def search_by_hashtag(
    db: AsyncSession,
    hashtag: str,
    limit: int | None = None,
    offset: int = 0,
) -> list[Post]:
    """Search posts by hashtag using GIN index @> operator.

    Hashtag is lowercased for case-insensitive matching.
    """
    if limit is None:
        limit = settings.search_default_limit
    limit = min(limit, settings.search_max_limit)

    normalized = hashtag.lower().strip()

    # Use PostgreSQL @> array operator: hashtags @> ARRAY[:tag]
    # This leverages the GIN index on posts.hashtags
    result = await db.execute(
        select(Post)
        .where(Post.hashtags.contains([normalized]))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())

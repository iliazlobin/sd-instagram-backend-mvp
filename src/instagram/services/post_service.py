"""Post service — create, get post, fan-out."""

import os
import re
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.config import settings
from instagram.models.feed_entry import FeedEntry
from instagram.models.follow import Follow
from instagram.models.post import Post

HASHTAG_RE = re.compile(r"#(\w+)")


def extract_hashtags(caption: str) -> list[str]:
    """Extract unique lowercase hashtags from a caption."""
    tags = HASHTAG_RE.findall(caption)
    # Lowercase and deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(lower)
    return result


def make_media_path(file_ext: str = ".jpg") -> str:
    """Generate a unique media path relative to media root."""
    filename = f"{uuid.uuid4().hex}{file_ext}"
    return f"/media/{filename}"


async def create_post(
    db: AsyncSession,
    user_id: UUID,
    caption: str,
    image_bytes: bytes,
    content_type: str,
) -> Post:
    """Create a post: save image, insert post row, fan-out to followers.

    Raises:
        FileTooLargeError: if image exceeds max_upload_bytes
        UserNotFoundError: if user_id does not exist
    """
    # Check file size
    if len(image_bytes) > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"Image too large: {len(image_bytes)} bytes (max {settings.max_upload_bytes})"
        )

    # Extract hashtags
    hashtags = extract_hashtags(caption)

    # Determine file extension from content_type
    ext_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    file_ext = ext_map.get(content_type, ".jpg")

    # Save image to disk
    media_dir = settings.media_dir
    os.makedirs(media_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(media_dir, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    media_url = f"/media/{filename}"

    # Insert post
    post = Post(
        post_id=uuid.uuid4(),
        user_id=user_id,
        caption=caption,
        media_url=media_url,
        media_type="photo",
        hashtags=hashtags,
        like_count=0,
    )
    db.add(post)
    await db.flush()

    # Fan-out: insert feed entries for all followers
    follower_result = await db.execute(
        select(Follow.follower_id).where(Follow.followed_id == user_id)
    )
    follower_ids = [row[0] for row in follower_result.fetchall()]

    if follower_ids:
        # Use raw SQL for efficient batch insert
        for fid in follower_ids:
            entry = FeedEntry(
                user_id=fid,
                post_id=post.post_id,
                author_id=user_id,
            )
            db.add(entry)
        await db.flush()

    await db.refresh(post)
    return post


async def get_post(db: AsyncSession, post_id: UUID) -> Post | None:
    """Get a post by ID."""
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    return result.scalar_one_or_none()


async def get_user_posts(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[Post]:
    """Get paginated posts for a user, newest first."""
    result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


class FileTooLargeError(ValueError):
    """Raised when uploaded file exceeds size limit."""

    pass


class UserNotFoundError(ValueError):
    """Raised when a referenced user does not exist."""

    pass

"""ORM models — one module per table."""

from instagram.database import Base
from instagram.models.feed_entry import FeedEntry
from instagram.models.follow import Follow
from instagram.models.like import Like
from instagram.models.post import Post
from instagram.models.user import User

__all__ = ["Base", "User", "Post", "Follow", "FeedEntry", "Like"]

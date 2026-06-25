"""Business logic + data access — routers delegate here."""

from instagram.services import (
    feed_service,
    follow_service,
    like_service,
    post_service,
    search_service,
    user_service,
)

__all__ = [
    "user_service",
    "post_service",
    "follow_service",
    "feed_service",
    "search_service",
    "like_service",
]

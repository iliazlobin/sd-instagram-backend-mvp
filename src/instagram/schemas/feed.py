"""Feed/search list schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserPostsResponse(BaseModel):
    """Post list item without author nesting (user context is implicit)."""

    post_id: UUID
    user_id: UUID
    caption: str
    media_url: str
    media_type: str
    hashtags: list[str]
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

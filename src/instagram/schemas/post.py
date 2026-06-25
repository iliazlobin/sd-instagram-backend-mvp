"""Post request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PostResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    caption: str
    media_url: str
    media_type: str
    hashtags: list[str]
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedPostResponse(BaseModel):
    """Post as it appears in a user's feed — includes author info."""

    post_id: UUID
    user_id: UUID
    caption: str
    media_url: str
    media_type: str
    hashtags: list[str]
    like_count: int
    created_at: datetime
    author: "UserBriefResponse"

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    user_id: UUID
    username: str
    display_name: str

    model_config = {"from_attributes": True}

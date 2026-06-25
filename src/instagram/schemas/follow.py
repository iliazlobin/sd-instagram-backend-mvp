"""Follow request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FollowResponse(BaseModel):
    follower_id: UUID
    followed_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}

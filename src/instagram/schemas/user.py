"""User request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=256)


class UserResponse(BaseModel):
    user_id: UUID
    username: str
    display_name: str
    follower_count: int
    following_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

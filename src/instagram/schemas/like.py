"""Like request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LikeResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}

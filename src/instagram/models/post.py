"""Post ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from instagram.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("users.user_id"), nullable=False, index=True
    )
    caption: Mapped[str] = mapped_column(Text(), nullable=False)
    media_url: Mapped[str] = mapped_column(Text(), nullable=False)
    media_type: Mapped[str] = mapped_column(Text(), nullable=False, server_default="photo")
    hashtags: Mapped[list] = mapped_column(ARRAY(Text()), nullable=False, server_default="{}")
    like_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

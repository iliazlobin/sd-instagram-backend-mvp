"""User ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from instagram.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    username: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    following_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

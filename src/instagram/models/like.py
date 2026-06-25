"""Like ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from instagram.database import Base


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (PrimaryKeyConstraint("post_id", "user_id"),)

    post_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("posts.post_id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

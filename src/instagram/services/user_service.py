"""User service — create, get user."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.models.user import User


async def create_user(db: AsyncSession, username: str, display_name: str) -> User:
    """Create a new user. Raises ValueError on duplicate username."""
    # Check for duplicate username
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise DuplicateUsernameError(f"Username '{username}' already taken")

    user = User(
        user_id=uuid4(),
        username=username,
        display_name=display_name,
    )
    db.add(user)
    await db.flush()
    return user


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


class DuplicateUsernameError(ValueError):
    """Raised when a username is already taken."""

    pass

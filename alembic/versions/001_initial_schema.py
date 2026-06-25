"""Initial schema — users, posts, follows, feed_entries, likes.

All five tables, composite primary keys for idempotency, GIN index on hashtags,
denormalized counters, and referential integrity.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "user_id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "follower_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "following_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── posts ───────────────────────────────────────────────────
    op.create_table(
        "posts",
        sa.Column(
            "post_id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("media_url", sa.Text(), nullable=False),
        sa.Column(
            "media_type",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'photo'"),
        ),
        sa.Column(
            "hashtags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "like_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_posts_user_created",
        "posts",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_posts_hashtags",
        "posts",
        ["hashtags"],
        postgresql_using="gin",
    )

    # ── follows ─────────────────────────────────────────────────
    op.create_table(
        "follows",
        sa.Column(
            "follower_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "followed_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("follower_id", "followed_id"),
    )

    # ── feed_entries ────────────────────────────────────────────
    op.create_table(
        "feed_entries",
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "post_id",
            postgresql.UUID(),
            sa.ForeignKey("posts.post_id"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("user_id", "created_at", "post_id"),
    )
    op.create_index(
        "idx_feed_user_created",
        "feed_entries",
        ["user_id", sa.text("created_at DESC")],
    )

    # ── likes ───────────────────────────────────────────────────
    op.create_table(
        "likes",
        sa.Column(
            "post_id",
            postgresql.UUID(),
            sa.ForeignKey("posts.post_id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )

    # ── CHECK constraint on posts.media_type ────────────────────
    op.create_check_constraint(
        "ck_posts_media_type",
        "posts",
        "media_type = 'photo'",
    )


def downgrade() -> None:
    op.drop_table("likes")
    op.drop_table("feed_entries")
    op.drop_table("follows")
    op.drop_table("posts")
    op.drop_table("users")

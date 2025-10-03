"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-03 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, UUID

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("metadata", JSON, default={}),
    )

    op.create_table(
        "stories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("hotness_score", sa.Float, nullable=False, default=0.0),
        sa.Column("why_now", sa.Text, nullable=True),
        sa.Column("sources", JSON, default=[]),
        sa.Column("timeline", JSON, default=[]),
        sa.Column("draft", sa.Text, nullable=True),
        sa.Column("news_count", sa.Integer, default=0),
        sa.Column("created_at", TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("idx_stories_hotness", "stories", ["hotness_score"])
    op.create_index("idx_stories_created_at", "stories", ["created_at"])

    op.create_table(
        "news",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False, unique=True),
        sa.Column("published_at", TIMESTAMP, nullable=False),
        sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("stories.id"), nullable=True),
        sa.Column("metadata", JSON, default={}),
        sa.Column("created_at", TIMESTAMP, server_default=sa.func.now()),
    )

    op.create_index("idx_news_cluster_id", "news", ["cluster_id"])
    op.create_index("idx_news_published_at", "news", ["published_at"])
    op.create_index("idx_news_source", "news", ["source"])

    op.create_table(
        "story_entities",
        sa.Column("story_id", UUID(as_uuid=True), sa.ForeignKey("stories.id"), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id"), primary_key=True),
    )

    op.create_table(
        "timelines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("story_id", UUID(as_uuid=True), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("timestamp", TIMESTAMP, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("metadata", JSON, default={}),
    )

    op.create_index("idx_timelines_story_id", "timelines", ["story_id"])

    op.create_table(
        "source_reputations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.String(100), nullable=False, unique=True),
        sa.Column("reputation_score", sa.Float, nullable=False, default=0.5),
        sa.Column("trust_level", sa.String(20), nullable=False, default="unknown"),
        sa.Column("verification_count", sa.Integer, default=0),
        sa.Column("updated_at", TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("source_reputations")
    op.drop_table("timelines")
    op.drop_table("story_entities")
    op.drop_table("news")
    op.drop_table("stories")
    op.drop_table("entities")


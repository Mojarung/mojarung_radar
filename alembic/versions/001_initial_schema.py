"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-10-03 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('reputation_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=True)

    op.create_table('stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('headline', sa.String(), nullable=False),
        sa.Column('hotness_score', sa.Float(), nullable=True),
        sa.Column('why_now', sa.String(), nullable=True),
        sa.Column('entities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timeline', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('draft', sa.String(), nullable=True),
        sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stories_created_at'), 'stories', ['created_at'], unique=False)
    op.create_index(op.f('ix_stories_hotness_score'), 'stories', ['hotness_score'], unique=False)

    op.create_table('news',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_published_at'), 'news', ['published_at'], unique=False)
    op.create_index(op.f('ix_news_url'), 'news', ['url'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_news_url'), table_name='news')
    op.drop_index(op.f('ix_news_published_at'), table_name='news')
    op.drop_table('news')
    
    op.drop_index(op.f('ix_stories_hotness_score'), table_name='stories')
    op.drop_index(op.f('ix_stories_created_at'), table_name='stories')
    op.drop_table('stories')
    
    op.drop_index(op.f('ix_sources_name'), table_name='sources')
    op.drop_table('sources')


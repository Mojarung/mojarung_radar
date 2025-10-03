"""Add timezone support to datetime columns

Revision ID: 002
Revises: 001
Create Date: 2025-10-03 19:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Изменяем тип колонок на TIMESTAMP WITH TIME ZONE
    op.execute("ALTER TABLE news ALTER COLUMN published_at TYPE TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE news ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    # Возвращаем обратно к TIMESTAMP WITHOUT TIME ZONE
    op.execute("ALTER TABLE news ALTER COLUMN published_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE news ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")

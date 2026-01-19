"""rename table

Revision ID: 6c5a06f3afec
Revises: 4c8f110e9c1a
Create Date: 2026-01-19 13:40:11.829960

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c5a06f3afec"
down_revision: Union[str, Sequence[str], None] = "4c8f110e9c1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("judge_results", "judges")


def downgrade() -> None:
    op.rename_table("judges", "judge_results")

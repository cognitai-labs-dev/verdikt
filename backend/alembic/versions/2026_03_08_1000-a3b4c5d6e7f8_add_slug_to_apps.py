"""add slug to apps

Revision ID: a3b4c5d6e7f8
Revises: e75178bca5b8
Create Date: 2026-03-08 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "e75178bca5b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "apps",
        sa.Column("slug", sa.String(100), nullable=True),
    )
    # Backfill existing rows using the app id so the NOT NULL constraint can be applied
    op.execute("UPDATE apps SET slug = 'app-' || id WHERE slug IS NULL")
    op.alter_column("apps", "slug", nullable=False)
    op.create_unique_constraint("uq_apps_slug", "apps", ["slug"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_apps_slug", "apps", type_="unique")
    op.drop_column("apps", "slug")

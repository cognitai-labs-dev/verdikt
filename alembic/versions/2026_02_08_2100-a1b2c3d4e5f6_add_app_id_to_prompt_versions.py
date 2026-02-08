"""add app_id to prompt_versions

Revision ID: a1b2c3d4e5f6
Revises: 206a1cd525d7
Create Date: 2026-02-08 21:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "206a1cd525d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add app_id column as nullable first
    op.add_column(
        "prompt_versions",
        sa.Column("app_id", sa.Integer(), nullable=True),
    )

    # Backfill: set app_id from apps.current_prompt_version_id
    op.execute(
        """
        UPDATE prompt_versions pv
        SET app_id = a.id
        FROM apps a
        WHERE a.current_prompt_version_id = pv.id
        """
    )

    # Make app_id NOT NULL
    op.alter_column(
        "prompt_versions",
        "app_id",
        nullable=False,
    )

    # Add FK constraint
    op.create_foreign_key(
        op.f("fk_prompt_versions_app_id_apps"),
        "prompt_versions",
        "apps",
        ["app_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop unique constraint on hash
    op.drop_constraint(
        op.f("uq_prompt_versions_hash"),
        "prompt_versions",
        type_="unique",
    )

    # Add unique constraint on (app_id, hash)
    op.create_unique_constraint(
        op.f("uq_prompt_versions_app_id_hash"),
        "prompt_versions",
        ["app_id", "hash"],
    )

    # Make apps.current_prompt_version_id nullable
    op.alter_column(
        "apps",
        "current_prompt_version_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # Add CASCADE to judgments.prompt_version_id FK
    op.drop_constraint(
        op.f("fk_judgments_prompt_version_id_prompt_versions"),
        "judgments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_judgments_prompt_version_id_prompt_versions"),
        "judgments",
        "prompt_versions",
        ["prompt_version_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Restore judgments FK without CASCADE
    op.drop_constraint(
        op.f("fk_judgments_prompt_version_id_prompt_versions"),
        "judgments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_judgments_prompt_version_id_prompt_versions"),
        "judgments",
        "prompt_versions",
        ["prompt_version_id"],
        ["id"],
    )

    # Make apps.current_prompt_version_id NOT NULL
    op.alter_column(
        "apps",
        "current_prompt_version_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Drop unique constraint on (app_id, hash)
    op.drop_constraint(
        op.f("uq_prompt_versions_app_id_hash"),
        "prompt_versions",
        type_="unique",
    )

    # Restore unique constraint on hash
    op.create_unique_constraint(
        op.f("uq_prompt_versions_hash"),
        "prompt_versions",
        ["hash"],
    )

    # Drop FK constraint
    op.drop_constraint(
        op.f("fk_prompt_versions_app_id_apps"),
        "prompt_versions",
        type_="foreignkey",
    )

    # Drop app_id column
    op.drop_column("prompt_versions", "app_id")

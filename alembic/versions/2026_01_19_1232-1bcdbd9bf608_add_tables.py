"""add tables

Revision ID: 1bcdbd9bf608
Revises:
Create Date: 2026-01-19 12:32:20.731224

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1bcdbd9bf608"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "evaluations",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column("app_id", sa.Integer, nullable=False),
        sa.Column(
            "app_version", sa.String(length=50), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluations")),
    )
    op.create_table(
        "samples",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("app_cost", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["evaluation_id"],
            ["evaluations.id"],
            name=op.f("fk_samples_evaluation_id_evaluations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_samples")),
    )
    op.create_table(
        "judgments",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "judgment_type", sa.String(length=50), nullable=False
        ),
        sa.Column(
            "judgment_model", sa.String(length=50), nullable=False
        ),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("input_tokens_cost", sa.Float(), nullable=True),
        sa.Column("output_tokens_cost", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sample_id"],
            ["samples.id"],
            name=op.f("fk_judgments_sample_id_samples"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_judgments")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("judgments")
    op.drop_table("samples")
    op.drop_table("evaluations")

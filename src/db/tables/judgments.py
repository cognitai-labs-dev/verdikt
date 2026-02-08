import sqlalchemy as sa

from src.db.pg import sa_metadata

judgments_table = sa.Table(
    "judgments",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "created_at",
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    ),
    sa.Column(
        "updated_at",
        sa.DateTime,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    ),
    sa.Column(
        "sample_id",
        sa.Integer,
        sa.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("status", sa.String(50), nullable=False),
    sa.Column("judgment_type", sa.String(50), nullable=False),
    sa.Column("judgment_model", sa.String(50), nullable=False),
    sa.Column("reasoning", sa.Text, nullable=True),
    sa.Column("passed", sa.Boolean, nullable=True),
    sa.Column("input_tokens", sa.Integer, nullable=True),
    sa.Column("output_tokens", sa.Integer, nullable=True),
    sa.Column("input_tokens_cost", sa.Float, nullable=True),
    sa.Column("output_tokens_cost", sa.Float, nullable=True),
    sa.Column(
        "prompt_version_id",
        sa.Integer,
        sa.ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
    ),
)

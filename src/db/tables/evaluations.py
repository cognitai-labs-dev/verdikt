import sqlalchemy as sa

from src.db.pg import sa_metadata

evaluations_table = sa.Table(
    "evaluations",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "app_id",
        sa.Integer,
        sa.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("version", sa.String(50), nullable=False),
    sa.Column("type", sa.String(50), nullable=False),
    sa.Column(
        "prompt_version_id",
        sa.Integer,
        sa.ForeignKey("prompt_versions.id"),
        nullable=True,
    ),
    sa.Column(
        "created_at",
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    ),
)

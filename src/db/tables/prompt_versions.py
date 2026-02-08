import sqlalchemy as sa

from src.db.pg import sa_metadata

prompt_versions_table = sa.Table(
    "prompt_versions",
    sa_metadata,
    sa.Column(
        "id",
        sa.Integer,
        primary_key=True,
        autoincrement=True,
    ),
    sa.Column(
        "app_id",
        sa.Integer,
        sa.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "hash",
        sa.String(64),
        nullable=False,
    ),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    ),
    sa.UniqueConstraint("app_id", "hash"),
)

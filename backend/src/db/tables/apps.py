import sqlalchemy as sa

from src.db.pg import sa_metadata

apps_table = sa.Table(
    "apps",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(100), nullable=False),
    sa.Column("slug", sa.String(100), nullable=False, unique=True),
    sa.Column(
        "current_prompt_version_id",
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

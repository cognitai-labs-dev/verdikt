import sqlalchemy as sa

from src.db.pg import sa_metadata

evaluation_runs_table = sa.Table(
    "evaluation_runs",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("app_id", sa.String(100), nullable=False),
    sa.Column("app_version", sa.String(50), nullable=False),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    sa.Column("metadata", sa.JSON, nullable=True),
)

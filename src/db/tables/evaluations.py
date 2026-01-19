import sqlalchemy as sa

from src.db.pg import sa_metadata


evaluations_table = sa.Table(
    "evaluations",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "run_id", sa.Integer, sa.ForeignKey("evaluation_runs.id"), nullable=False
    ),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    sa.Column("question", sa.Text, nullable=False),
    sa.Column("answer", sa.Text, nullable=False),
    sa.Column("app_cost", sa.Float, nullable=True),
    sa.Column("metadata", sa.JSON, nullable=True),
)

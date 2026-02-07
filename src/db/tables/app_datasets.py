import sqlalchemy as sa

from src.db.pg import sa_metadata

app_datasets_table = sa.Table(
    "app_datasets",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("question", sa.Text, nullable=False),
    sa.Column("human_answer", sa.Text, nullable=False),
    sa.Column(
        "app_id",
        sa.Integer,
        sa.ForeignKey("apps.id"),
        nullable=False,
    ),
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
)

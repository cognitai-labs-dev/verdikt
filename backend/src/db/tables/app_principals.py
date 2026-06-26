import sqlalchemy as sa

from src.db.pg import sa_metadata

app_principals_table = sa.Table(
    "app_principals",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "app_id",
        sa.Integer,
        sa.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("subject_type", sa.String(50), nullable=False),
    sa.Column("subject", sa.String(255), nullable=False),
    sa.UniqueConstraint("app_id", "subject_type", "subject"),
)

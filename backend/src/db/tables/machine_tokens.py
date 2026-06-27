import sqlalchemy as sa

from src.db.pg import sa_metadata

machine_tokens_table = sa.Table(
    "machine_tokens",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "token_hash", sa.String(64), nullable=False, unique=True
    ),
    sa.Column(
        "client_id",
        sa.String(100),
        sa.ForeignKey(
            "machine_clients.client_id", ondelete="CASCADE"
        ),
        nullable=False,
    ),
    sa.Column("expires_at", sa.DateTime, nullable=False),
    sa.Column(
        "revoked",
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    ),
    sa.Column(
        "created_at",
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    ),
)

import sqlalchemy as sa

from src.db.pg import sa_metadata

machine_clients_table = sa.Table(
    "machine_clients",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "client_id", sa.String(100), nullable=False, unique=True
    ),
    sa.Column("client_secret_hash", sa.String(64), nullable=False),
    sa.Column("name", sa.String(100), nullable=False),
    sa.Column(
        "is_admin",
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    ),
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

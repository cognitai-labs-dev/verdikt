import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth.hashing import sha256_hex, utcnow
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from src.schemas.machine_token import MachineTokenCreateSchema

TOKEN_PREFIX = "vkt_"


class AuthCommands:
    """Verdikt's own OAuth2 client_credentials issuer (opaque tokens)."""

    def __init__(
        self,
        machine_client_repo: MachineClientRepository,
        machine_token_repo: MachineTokenRepository,
        token_ttl: int,
    ):
        self.machine_client_repo = machine_client_repo
        self.machine_token_repo = machine_token_repo
        self.token_ttl = token_ttl

    async def issue_machine_token(
        self,
        conn: AsyncConnection,
        client_id: str,
        client_secret: str,
    ) -> tuple[str, int]:
        """Validate client credentials and mint an opaque DB-backed token.

        Returns `(raw_token, ttl_seconds)`. Raises `ValueError("invalid_client")`
        when the client is missing, revoked, or the secret does not match.
        """
        client = await self.machine_client_repo.get_by_client_id(
            conn, client_id
        )
        if client is None or client.revoked:
            raise ValueError("invalid_client")

        if not secrets.compare_digest(
            client.client_secret_hash, sha256_hex(client_secret)
        ):
            raise ValueError("invalid_client")

        raw_token = TOKEN_PREFIX + secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(seconds=self.token_ttl)
        await self.machine_token_repo.create(
            conn,
            MachineTokenCreateSchema(
                token_hash=sha256_hex(raw_token),
                client_id=client_id,
                expires_at=expires_at,
            ),
        )
        return raw_token, self.token_ttl

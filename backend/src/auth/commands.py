import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth.hashing import sha256_hex, utcnow
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.apps import AppsRepository
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from src.schemas.machine_client import (
    MachineClientCreateSchema,
    MachineClientSchema,
)
from src.schemas.machine_token import MachineTokenCreateSchema

TOKEN_PREFIX = "vkt_"
CLIENT_ID_PREFIX = "mc_"
CLIENT_SECRET_PREFIX = "secret_"


class AuthCommands:
    """Verdikt's own OAuth2 client_credentials issuer (opaque tokens)."""

    def __init__(
        self,
        machine_client_repo: MachineClientRepository,
        machine_token_repo: MachineTokenRepository,
        token_ttl: int,
        app_repo: AppsRepository | None = None,
        app_principal_repo: AppPrincipalRepository | None = None,
    ):
        self.machine_client_repo = machine_client_repo
        self.machine_token_repo = machine_token_repo
        self.token_ttl = token_ttl
        self.app_repo = app_repo
        self.app_principal_repo = app_principal_repo

    async def create_machine_client(
        self,
        conn: AsyncConnection,
        name: str,
        is_admin: bool,
        app_slugs: list[str],
    ) -> tuple[MachineClientSchema, str]:
        """Mint a new machine client, hash its secret, persist and bind apps.

        Returns ``(MachineClientSchema, raw_secret)``. The raw secret is
        returned exactly once and never stored in plaintext.

        Raises ``ValueError`` if any slug in ``app_slugs`` does not resolve.
        """
        if self.app_repo is None or self.app_principal_repo is None:
            raise RuntimeError(
                "create_machine_client requires app_repo and app_principal_repo"
            )

        client_id = CLIENT_ID_PREFIX + secrets.token_urlsafe(12)
        raw_secret = CLIENT_SECRET_PREFIX + secrets.token_urlsafe(32)

        client = await self.machine_client_repo.create(
            conn,
            MachineClientCreateSchema(
                client_id=client_id,
                client_secret_hash=sha256_hex(raw_secret),
                name=name,
                is_admin=is_admin,
            ),
        )

        for slug in app_slugs:
            app = await self.app_repo.get_by_slug(conn, slug)
            if app is None:
                raise ValueError(f"app '{slug}' not found")
            await self.app_principal_repo.add(
                conn, app.id, SubjectType.CLIENT, client_id
            )

        return client, raw_secret

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

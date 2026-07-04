from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api import deps
from src.api.deps import authenticate
from src.auth.access_config import AdminRegistry
from src.auth.commands import AuthCommands
from src.auth.hashing import sha256_hex, utcnow
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.apps import AppsRepository
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from src.schemas.machine_token import MachineTokenCreateSchema
from tests.factories.machine_client import machine_client_db_factory


def _registry() -> AdminRegistry:
    return AdminRegistry(
        app_repo=AppsRepository(),
        app_principal_repo=AppPrincipalRepository(),
    )


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _fake_decode(claims: dict):
    async def _decode(token: str) -> dict:
        return claims

    return _decode


@pytest.mark.anyio
async def test_authenticate_valid_machine_token_returns_client_principal(
    db_conn: AsyncConnection,
):
    # Arrange — admin machine client with a freshly issued token
    await machine_client_db_factory(
        db_conn, client_id="mc-admin", secret="s", is_admin=True
    )
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), MachineTokenRepository(), 3600
    ).issue_machine_token(db_conn, "mc-admin", "s")

    # Act
    principal = await authenticate(_creds(raw_token), db_conn)

    # Assert
    assert principal.subject == "mc-admin"
    assert principal.subject_type == SubjectType.CLIENT
    assert principal.is_admin is True


@pytest.mark.anyio
async def test_authenticate_expired_machine_token_raises_401(
    db_conn: AsyncConnection,
):
    # Arrange — a token row whose expiry is in the past
    await machine_client_db_factory(
        db_conn, client_id="mc-exp", secret="s"
    )
    raw_token = "vkt_expired-token-value"
    await MachineTokenRepository().create(
        db_conn,
        MachineTokenCreateSchema(
            token_hash=sha256_hex(raw_token),
            client_id="mc-exp",
            expires_at=utcnow() - timedelta(hours=1),
        ),
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        await authenticate(_creds(raw_token), db_conn)
    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_authenticate_revoked_machine_token_raises_401(
    db_conn: AsyncConnection,
):
    # Arrange
    await machine_client_db_factory(
        db_conn, client_id="mc-rev", secret="s"
    )
    token_repo = MachineTokenRepository()
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), token_repo, 3600
    ).issue_machine_token(db_conn, "mc-rev", "s")
    await token_repo.revoke_for_client(db_conn, "mc-rev")

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        await authenticate(_creds(raw_token), db_conn)
    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_authenticate_human_token_returns_email_principal(
    db_conn: AsyncConnection, monkeypatch
):
    # Arrange — non-vkt token routes to the human path; verifier is stubbed
    monkeypatch.setattr(deps, "admin_registry", _registry())
    monkeypatch.setattr(
        deps.token_verifier,
        "decoded_token",
        _fake_decode({"email": "person@example.com"}),
    )

    # Act
    principal = await authenticate(_creds("header.payload.sig"), db_conn)

    # Assert
    assert principal.subject == "person@example.com"
    assert principal.subject_type == SubjectType.EMAIL
    assert principal.is_admin is False


@pytest.mark.anyio
async def test_authenticate_human_token_admin_email_is_admin(
    db_conn: AsyncConnection, monkeypatch
):
    # Arrange — the email claim is an admin in the access-config registry
    registry = _registry()
    registry.replace(["boss@example.com"])
    monkeypatch.setattr(deps, "admin_registry", registry)
    monkeypatch.setattr(
        deps.token_verifier,
        "decoded_token",
        _fake_decode({"email": "boss@example.com"}),
    )

    # Act
    principal = await authenticate(_creds("header.payload.sig"), db_conn)

    # Assert
    assert principal.is_admin is True

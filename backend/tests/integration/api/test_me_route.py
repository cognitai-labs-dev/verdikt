from typing import AsyncIterator

import httpx
import jwt
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api import deps
from src.api_app import api_factory
from src.auth.commands import AuthCommands
from src.constants import SubjectType
from src.dependencies import get_connection
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from tests.factories.machine_client import machine_client_db_factory


def _build_client(db_conn: AsyncConnection) -> httpx.AsyncClient:
    """An HTTP client over the real ASGI app, wired to the test connection."""
    app = api_factory()

    async def _conn() -> AsyncIterator[AsyncConnection]:
        yield db_conn

    app.dependency_overrides[get_connection] = _conn
    return httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    )


@pytest.mark.anyio
async def test_get_me_without_token_returns_401(
    db_conn: AsyncConnection,
):
    # Arrange
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get("/v1/me")

    # Assert
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_me_with_invalid_token_returns_401(
    db_conn: AsyncConnection, monkeypatch
):
    # Arrange — a non-vkt token routes to the human path; the verifier rejects
    # it (stubbed so the test never reaches out to the OIDC issuer).
    async def _reject(_token: str) -> dict:
        raise jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(deps.token_verifier, "decoded_token", _reject)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            "/v1/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )

    # Assert
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_me_returns_identity_for_authenticated_client(
    db_conn: AsyncConnection,
):
    # Arrange — a non-admin machine client with a freshly issued token
    await machine_client_db_factory(
        db_conn, client_id="mc-me", secret="s", is_admin=False
    )
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), MachineTokenRepository(), 3600
    ).issue_machine_token(db_conn, "mc-me", "s")
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "subject": "mc-me",
        "subject_type": SubjectType.CLIENT,
        "is_admin": False,
    }


@pytest.mark.anyio
async def test_get_me_returns_admin_flag_for_admin_client(
    db_conn: AsyncConnection,
):
    # Arrange — an admin machine client with a freshly issued token
    await machine_client_db_factory(
        db_conn, client_id="mc-me-admin", secret="s", is_admin=True
    )
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), MachineTokenRepository(), 3600
    ).issue_machine_token(db_conn, "mc-me-admin", "s")
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "subject": "mc-me-admin",
        "subject_type": SubjectType.CLIENT,
        "is_admin": True,
    }

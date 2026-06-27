from typing import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api_app import api_factory
from src.auth.commands import AuthCommands
from src.dependencies import get_connection
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from tests.factories.app import app_db_schema_factory
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


async def _token_for(
    db_conn: AsyncConnection, client_id: str, *, is_admin: bool
) -> str:
    """Create a machine client and return a freshly issued bearer token."""
    await machine_client_db_factory(
        db_conn, client_id=client_id, secret="s", is_admin=is_admin
    )
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), MachineTokenRepository(), 3600
    ).issue_machine_token(db_conn, client_id, "s")
    return raw_token


@pytest.mark.anyio
async def test_list_machine_clients_forbidden_for_non_admin(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-plain", is_admin=False)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            "/v1/admin/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert
    assert response.status_code == 403


@pytest.mark.anyio
async def test_list_machine_clients_allowed_for_admin(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-admin", is_admin=True)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            "/v1/admin/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert
    assert response.status_code == 200
    client_ids = {row["client_id"] for row in response.json()}
    assert "mc-admin" in client_ids


@pytest.mark.anyio
async def test_create_machine_client_returns_secret_once(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-creator", is_admin=True)
    app = await app_db_schema_factory(db_conn)
    client = _build_client(db_conn)

    # Act — create, then list
    async with client:
        created = await client.post(
            "/v1/admin/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "new-client",
                "is_admin": False,
                "app_slugs": [app.slug],
            },
        )
        listed = await client.get(
            "/v1/admin/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert — secret present on create, app bound, secret absent from list
    assert created.status_code == 201
    body = created.json()
    assert body["client_secret"].startswith("secret_")
    assert app.id in {a["id"] for a in body["apps"]}
    new_client_id = body["client_id"]
    listed_row = next(
        row
        for row in listed.json()
        if row["client_id"] == new_client_id
    )
    assert "client_secret" not in listed_row


@pytest.mark.anyio
async def test_create_machine_client_unknown_slug_returns_400(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-creator-2", is_admin=True)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.post(
            "/v1/admin/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "bad",
                "is_admin": False,
                "app_slugs": ["does-not-exist"],
            },
        )

    # Assert
    assert response.status_code == 400


@pytest.mark.anyio
async def test_revoke_machine_client_kills_live_tokens(
    db_conn: AsyncConnection,
):
    # Arrange — admin to call the API, plus a victim client with a live token
    admin_token = await _token_for(db_conn, "mc-admin-rev", is_admin=True)
    victim_token = await _token_for(db_conn, "mc-victim", is_admin=False)
    client = _build_client(db_conn)

    # Act — revoke the victim, then the victim tries to use its token
    async with client:
        revoke = await client.post(
            "/v1/admin/machine-clients/mc-victim/revoke",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        after = await client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {victim_token}"},
        )

    # Assert
    assert revoke.status_code == 200
    assert revoke.json()["revoked"] is True
    assert after.status_code == 401


@pytest.mark.anyio
async def test_revoke_unknown_client_returns_404(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-admin-404", is_admin=True)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.post(
            "/v1/admin/machine-clients/mc-nope/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert
    assert response.status_code == 404


@pytest.mark.anyio
async def test_bind_then_unbind_app_reflected_in_response(
    db_conn: AsyncConnection,
):
    # Arrange
    token = await _token_for(db_conn, "mc-admin-bind", is_admin=True)
    await machine_client_db_factory(
        db_conn, client_id="mc-bindable", secret="s", is_admin=False
    )
    app = await app_db_schema_factory(db_conn)
    client = _build_client(db_conn)

    # Act
    async with client:
        bound = await client.post(
            "/v1/admin/machine-clients/mc-bindable/apps",
            headers={"Authorization": f"Bearer {token}"},
            json={"app_id": app.id},
        )
        unbound = await client.delete(
            f"/v1/admin/machine-clients/mc-bindable/apps/{app.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert
    assert bound.status_code == 201
    assert app.id in {a["id"] for a in bound.json()["apps"]}
    assert unbound.status_code == 200
    assert app.id not in {a["id"] for a in unbound.json()["apps"]}

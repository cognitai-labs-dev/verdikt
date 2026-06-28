from typing import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api_app import api_factory
from src.auth.commands import AuthCommands
from src.constants import SubjectType
from src.dependencies import get_connection
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.machine_client import machine_client_db_factory


def _build_client(db_conn: AsyncConnection) -> httpx.AsyncClient:
    app = api_factory()

    async def _conn() -> AsyncIterator[AsyncConnection]:
        yield db_conn

    app.dependency_overrides[get_connection] = _conn
    return httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    )


async def _actor_token_bound_to(
    db_conn: AsyncConnection, client_id: str, app_id: int | None
) -> str:
    """A machine client (optionally bound to app_id) with a fresh token."""
    await machine_client_db_factory(
        db_conn, client_id=client_id, secret="s", is_admin=False
    )
    if app_id is not None:
        await AppPrincipalRepository().add(
            db_conn, app_id, SubjectType.CLIENT, client_id
        )
    raw_token, _ = await AuthCommands(
        MachineClientRepository(), MachineTokenRepository(), 3600
    ).issue_machine_token(db_conn, client_id, "s")
    return raw_token


@pytest.mark.anyio
async def test_app_machine_clients_forbidden_for_non_member(
    db_conn: AsyncConnection,
):
    # Arrange — actor client is NOT bound to the app
    app = await app_db_schema_factory(db_conn)
    token = await _actor_token_bound_to(db_conn, "mc-outsider", None)
    client = _build_client(db_conn)

    # Act
    async with client:
        response = await client.get(
            f"/v1/app/{app.id}/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_app_machine_client_returns_secret_and_binds(
    db_conn: AsyncConnection,
):
    # Arrange — actor is a member of the app
    app = await app_db_schema_factory(db_conn)
    token = await _actor_token_bound_to(db_conn, "mc-member", app.id)
    client = _build_client(db_conn)

    # Act — create a client, then list
    async with client:
        created = await client.post(
            f"/v1/app/{app.id}/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "pipeline"},
        )
        listed = await client.get(
            f"/v1/app/{app.id}/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert — secret returned once, new client bound to this app, in the list
    assert created.status_code == 201
    body = created.json()
    assert body["client_secret"].startswith("secret_")
    new_client_id = body["client_id"]
    bound = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.CLIENT, new_client_id
    )
    assert bound == [app.id]
    assert new_client_id in {c["client_id"] for c in listed.json()}


@pytest.mark.anyio
async def test_delete_app_machine_client_unbinds_and_revokes_orphan(
    db_conn: AsyncConnection,
):
    # Arrange — a member creates a client bound only to this app
    app = await app_db_schema_factory(db_conn)
    token = await _actor_token_bound_to(db_conn, "mc-owner", app.id)
    client = _build_client(db_conn)

    async with client:
        created = await client.post(
            f"/v1/app/{app.id}/machine-clients",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "to-delete"},
        )
        target_id = created.json()["client_id"]

        # Act
        deleted = await client.delete(
            f"/v1/app/{app.id}/machine-clients/{target_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Assert — unbound from the app and revoked (it had no other app)
    assert deleted.status_code == 204
    bound = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.CLIENT, target_id
    )
    assert bound == []
    stored = await MachineClientRepository().get_by_client_id(
        db_conn, target_id
    )
    assert stored is not None
    assert stored.revoked is True

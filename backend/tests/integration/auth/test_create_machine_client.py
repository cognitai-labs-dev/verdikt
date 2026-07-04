import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth.commands import AuthCommands
from src.auth.hashing import sha256_hex
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from src.repositories.apps import AppsRepository
from tests.factories.app import app_db_schema_factory


def _commands() -> AuthCommands:
    return AuthCommands(
        machine_client_repo=MachineClientRepository(),
        machine_token_repo=MachineTokenRepository(),
        token_ttl=3600,
        app_repo=AppsRepository(),
        app_principal_repo=AppPrincipalRepository(),
    )


@pytest.mark.anyio
async def test_create_machine_client_returns_schema_and_raw_secret(
    db_conn: AsyncConnection,
):
    # Arrange
    commands = _commands()

    # Act
    client, raw_secret = await commands.create_machine_client(
        db_conn, name="my-client", is_admin=False, app_slugs=[]
    )

    # Assert
    assert client.client_id.startswith("mc_")
    assert raw_secret.startswith("secret_")
    assert client.name == "my-client"
    assert client.is_admin is False


@pytest.mark.anyio
async def test_create_machine_client_stores_only_hash_not_plaintext(
    db_conn: AsyncConnection,
):
    # Arrange
    commands = _commands()

    # Act
    client, raw_secret = await commands.create_machine_client(
        db_conn, name="hash-check", is_admin=False, app_slugs=[]
    )

    # Assert — secret stored as hash, not plaintext
    stored = await MachineClientRepository().get_by_client_id(
        db_conn, client.client_id
    )
    assert stored is not None
    assert stored.client_secret_hash == sha256_hex(raw_secret)
    assert stored.client_secret_hash != raw_secret


@pytest.mark.anyio
async def test_create_machine_client_binds_each_requested_app(
    db_conn: AsyncConnection,
):
    # Arrange
    app_a = await app_db_schema_factory(db_conn)
    app_b = await app_db_schema_factory(db_conn)
    commands = _commands()

    # Act
    client, _ = await commands.create_machine_client(
        db_conn,
        name="bound-client",
        is_admin=False,
        app_slugs=[app_a.slug, app_b.slug],
    )

    # Assert
    bound_app_ids = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.CLIENT, client.client_id
    )
    assert app_a.id in bound_app_ids
    assert app_b.id in bound_app_ids


@pytest.mark.anyio
async def test_create_machine_client_unknown_slug_raises_value_error(
    db_conn: AsyncConnection,
):
    # Arrange
    commands = _commands()

    # Act / Assert
    with pytest.raises(ValueError, match="nonexistent-slug"):
        await commands.create_machine_client(
            db_conn,
            name="bad-client",
            is_admin=False,
            app_slugs=["nonexistent-slug"],
        )


@pytest.mark.anyio
async def test_create_machine_client_admin_does_not_bind_any_app(
    db_conn: AsyncConnection,
):
    # Arrange — admin flag; no app_slugs; admin clients see all apps without bindings
    commands = _commands()

    # Act
    client, _ = await commands.create_machine_client(
        db_conn, name="admin-client", is_admin=True, app_slugs=[]
    )

    # Assert
    assert client.is_admin is True
    bound_app_ids = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.CLIENT, client.client_id
    )
    assert bound_app_ids == []

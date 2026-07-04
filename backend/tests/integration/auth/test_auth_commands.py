import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth.commands import AuthCommands
from src.auth.hashing import sha256_hex
from src.constants import TOKEN_PREFIX
from src.repositories.machine_client import MachineClientRepository
from src.repositories.machine_token import MachineTokenRepository
from tests.factories.machine_client import machine_client_db_factory


def _commands(ttl: int = 3600) -> AuthCommands:
    return AuthCommands(
        MachineClientRepository(),
        MachineTokenRepository(),
        token_ttl=ttl,
    )


@pytest.mark.anyio
async def test_issue_machine_token_valid_credentials_returns_token_and_ttl(
    db_conn: AsyncConnection,
):
    # Arrange
    await machine_client_db_factory(
        db_conn, client_id="mc-valid", secret="s3cret"
    )
    commands = _commands(ttl=120)

    # Act
    raw_token, ttl = await commands.issue_machine_token(
        db_conn, "mc-valid", "s3cret"
    )

    # Assert
    assert raw_token.startswith(TOKEN_PREFIX)
    assert ttl == 120
    stored = await MachineTokenRepository().get_by_hash(
        db_conn, sha256_hex(raw_token)
    )
    assert stored is not None
    assert stored.client_id == "mc-valid"


@pytest.mark.anyio
async def test_issue_machine_token_unknown_client_raises_invalid_client(
    db_conn: AsyncConnection,
):
    # Arrange
    commands = _commands()

    # Act / Assert
    with pytest.raises(ValueError, match="invalid_client"):
        await commands.issue_machine_token(
            db_conn, "mc-missing", "whatever"
        )


@pytest.mark.anyio
async def test_issue_machine_token_wrong_secret_raises_invalid_client(
    db_conn: AsyncConnection,
):
    # Arrange
    await machine_client_db_factory(
        db_conn, client_id="mc-secret", secret="right-secret"
    )
    commands = _commands()

    # Act / Assert
    with pytest.raises(ValueError, match="invalid_client"):
        await commands.issue_machine_token(
            db_conn, "mc-secret", "wrong-secret"
        )


@pytest.mark.anyio
async def test_issue_machine_token_revoked_client_raises_invalid_client(
    db_conn: AsyncConnection,
):
    # Arrange
    await machine_client_db_factory(
        db_conn, client_id="mc-revoked", secret="s", revoked=True
    )
    commands = _commands()

    # Act / Assert
    with pytest.raises(ValueError, match="invalid_client"):
        await commands.issue_machine_token(db_conn, "mc-revoked", "s")

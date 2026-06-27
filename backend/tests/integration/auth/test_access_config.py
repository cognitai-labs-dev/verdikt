from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth import access_config
from src.auth.access_config import AccessConfig
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.apps import AppsRepository
from tests.factories.app import app_db_schema_factory


def _apps_repo() -> AppsRepository:
    return AppsRepository()


def test_load_parses_admins_and_app_bindings(tmp_path: Path):
    # Arrange
    cfg_file = tmp_path / "access.yaml"
    cfg_file.write_text(
        "admins:\n"
        "  - alice@example.com\n"
        "apps:\n"
        "  my-app:\n"
        "    - bob@example.com\n"
    )

    # Act
    cfg = access_config.load(str(cfg_file))

    # Assert
    assert cfg.admins == ["alice@example.com"]
    assert cfg.apps == {"my-app": ["bob@example.com"]}


def test_load_empty_file_yields_empty_config(tmp_path: Path):
    # Arrange
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")

    # Act
    cfg = access_config.load(str(cfg_file))

    # Assert
    assert cfg.admins == []
    assert cfg.apps == {}


@pytest.mark.anyio
async def test_reconcile_adds_missing_and_removes_extra_email_bindings(
    db_conn: AsyncConnection,
):
    # Arrange — app with one stale email binding and one CLIENT binding
    repo = AppPrincipalRepository()
    app = await app_db_schema_factory(db_conn)
    await repo.add(db_conn, app.id, SubjectType.EMAIL, "stale@example.com")
    await repo.add(db_conn, app.id, SubjectType.CLIENT, "mc-keep")
    cfg = AccessConfig(
        admins=[], apps={app.slug: ["new@example.com"]}
    )

    # Act
    await access_config.reconcile(
        db_conn, _apps_repo(), repo, cfg
    )

    # Assert — EMAIL bindings now match the file exactly; CLIENT untouched
    emails = set(
        await repo.subjects_for(db_conn, app.id, SubjectType.EMAIL)
    )
    clients = set(
        await repo.subjects_for(db_conn, app.id, SubjectType.CLIENT)
    )
    assert emails == {"new@example.com"}
    assert clients == {"mc-keep"}


@pytest.mark.anyio
async def test_reconcile_skips_unknown_app(db_conn: AsyncConnection):
    # Arrange
    cfg = AccessConfig(
        admins=[], apps={"does-not-exist": ["x@example.com"]}
    )

    # Act / Assert — no exception raised for a missing app
    await access_config.reconcile(
        db_conn, _apps_repo(), AppPrincipalRepository(), cfg
    )


@pytest.mark.anyio
async def test_reconcile_populates_admin_registry(
    db_conn: AsyncConnection,
):
    # Arrange
    cfg = AccessConfig(admins=["admin@example.com"], apps={})

    # Act
    await access_config.reconcile(
        db_conn, _apps_repo(), AppPrincipalRepository(), cfg
    )

    # Assert
    assert "admin@example.com" in access_config.admin_registry

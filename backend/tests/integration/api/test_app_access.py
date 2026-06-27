import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.deps import (
    Principal,
    allowed_app_ids,
    require_app_access,
    require_sample_access,
)
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.evaluation import evaluation_db_schema_factory
from tests.factories.sample import sample_db_schema_factory


def _client_principal(subject: str, is_admin: bool = False) -> Principal:
    return Principal(
        subject=subject,
        subject_type=SubjectType.CLIENT,
        is_admin=is_admin,
    )


@pytest.mark.anyio
async def test_allowed_app_ids_returns_none_for_admin(
    db_conn: AsyncConnection,
):
    # Arrange
    principal = _client_principal("mc-admin", is_admin=True)

    # Act
    ids = await allowed_app_ids(db_conn, principal)

    # Assert
    assert ids is None


@pytest.mark.anyio
async def test_allowed_app_ids_returns_only_bound_apps_for_member(
    db_conn: AsyncConnection,
):
    # Arrange
    bound_app = await app_db_schema_factory(db_conn, name="bound")
    # another app the member is NOT bound to
    await app_db_schema_factory(db_conn, name="other")
    await AppPrincipalRepository().add(
        db_conn, bound_app.id, SubjectType.CLIENT, "mc-member"
    )
    principal = _client_principal("mc-member")

    # Act
    ids = await allowed_app_ids(db_conn, principal)

    # Assert
    assert ids == [bound_app.id]


@pytest.mark.anyio
async def test_require_app_access_allows_bound_app(
    db_conn: AsyncConnection,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    await AppPrincipalRepository().add(
        db_conn, app.id, SubjectType.CLIENT, "mc-member"
    )
    principal = _client_principal("mc-member")

    # Act
    result = await require_app_access(app.id, principal, db_conn)

    # Assert
    assert result.subject == "mc-member"


@pytest.mark.anyio
async def test_require_app_access_forbids_unbound_app(
    db_conn: AsyncConnection,
):
    # Arrange — member bound to app_a tries app_b
    app_a = await app_db_schema_factory(db_conn, name="a")
    app_b = await app_db_schema_factory(db_conn, name="b")
    await AppPrincipalRepository().add(
        db_conn, app_a.id, SubjectType.CLIENT, "mc-member"
    )
    principal = _client_principal("mc-member")

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        await require_app_access(app_b.id, principal, db_conn)
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_require_app_access_allows_admin_any_app(
    db_conn: AsyncConnection,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    principal = _client_principal("mc-admin", is_admin=True)

    # Act
    result = await require_app_access(app.id, principal, db_conn)

    # Assert
    assert result.is_admin is True


@pytest.mark.anyio
async def test_require_sample_access_forbids_other_teams_sample(
    db_conn: AsyncConnection,
):
    # Arrange — sample belongs to app_b; member is bound only to app_a
    app_a = await app_db_schema_factory(db_conn, name="a")
    app_b = await app_db_schema_factory(db_conn, name="b")
    evaluation = await evaluation_db_schema_factory(
        db_conn, app_id=app_b.id
    )
    sample = await sample_db_schema_factory(
        db_conn, evaluation_id=evaluation.id
    )
    await AppPrincipalRepository().add(
        db_conn, app_a.id, SubjectType.CLIENT, "mc-member"
    )
    principal = _client_principal("mc-member")

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        await require_sample_access(sample.id, principal, db_conn)
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_require_sample_access_allows_owning_team(
    db_conn: AsyncConnection,
):
    # Arrange — member bound to the app that owns the sample
    app = await app_db_schema_factory(db_conn)
    evaluation = await evaluation_db_schema_factory(
        db_conn, app_id=app.id
    )
    sample = await sample_db_schema_factory(
        db_conn, evaluation_id=evaluation.id
    )
    await AppPrincipalRepository().add(
        db_conn, app.id, SubjectType.CLIENT, "mc-member"
    )
    principal = _client_principal("mc-member")

    # Act
    result = await require_sample_access(sample.id, principal, db_conn)

    # Assert
    assert result.subject == "mc-member"


@pytest.mark.anyio
async def test_require_sample_access_missing_sample_raises_404(
    db_conn: AsyncConnection,
):
    # Arrange
    principal = _client_principal("mc-member")

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        await require_sample_access(999999, principal, db_conn)
    assert exc.value.status_code == 404

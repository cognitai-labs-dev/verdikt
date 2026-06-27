import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.deps import Principal
from src.api.v1.routes.app import post_app
from src.api.v1.schemas import AppRequest
from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository


@pytest.mark.anyio
async def test_post_app_binds_non_admin_creator_to_new_app(
    db_conn: AsyncConnection,
):
    # Arrange
    principal = Principal(
        subject="mc-creator",
        subject_type=SubjectType.CLIENT,
        is_admin=False,
    )

    # Act
    app = await post_app(
        AppRequest(name="My App", slug="creator-bind-app"),
        principal,
        db_conn,
    )

    # Assert — creator can now access the app they made
    ids = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.CLIENT, "mc-creator"
    )
    assert app.id in ids


@pytest.mark.anyio
async def test_post_app_does_not_bind_admin_creator(
    db_conn: AsyncConnection,
):
    # Arrange — admins see every app, so no binding row is needed
    principal = Principal(
        subject="boss@example.com",
        subject_type=SubjectType.EMAIL,
        is_admin=True,
    )

    # Act
    app = await post_app(
        AppRequest(name="Admin App", slug="admin-bind-app"),
        principal,
        db_conn,
    )

    # Assert
    ids = await AppPrincipalRepository().app_ids_for(
        db_conn, SubjectType.EMAIL, "boss@example.com"
    )
    assert app.id not in ids

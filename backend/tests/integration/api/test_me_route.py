import pytest

from src.api.deps import Principal
from src.api.v1.routes.me import get_me
from src.constants import SubjectType


@pytest.mark.anyio
async def test_get_me_returns_identity_for_authenticated_principal():
    # Arrange
    principal = Principal(
        subject="mc-test",
        subject_type=SubjectType.CLIENT,
        is_admin=False,
    )

    # Act
    result = await get_me(principal)

    # Assert
    assert result.subject == "mc-test"
    assert result.subject_type == SubjectType.CLIENT
    assert result.is_admin is False


@pytest.mark.anyio
async def test_get_me_returns_admin_flag_for_admin_principal():
    # Arrange
    principal = Principal(
        subject="boss@example.com",
        subject_type=SubjectType.EMAIL,
        is_admin=True,
    )

    # Act
    result = await get_me(principal)

    # Assert
    assert result.subject == "boss@example.com"
    assert result.subject_type == SubjectType.EMAIL
    assert result.is_admin is True

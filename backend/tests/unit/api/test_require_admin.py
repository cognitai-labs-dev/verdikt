import pytest
from fastapi import HTTPException

from src.api.deps import Principal, require_admin
from src.constants import SubjectType


def _principal(is_admin: bool) -> Principal:
    return Principal(
        subject="test-subject",
        subject_type=SubjectType.CLIENT,
        is_admin=is_admin,
    )


def test_require_admin_allows_admin_principal():
    # Arrange
    principal = _principal(is_admin=True)

    # Act
    result = require_admin(principal)

    # Assert
    assert result is principal


def test_require_admin_forbids_non_admin_principal():
    # Arrange
    principal = _principal(is_admin=False)

    # Act / Assert
    with pytest.raises(HTTPException) as exc:
        require_admin(principal)
    assert exc.value.status_code == 403
    assert exc.value.detail == "Admin access required"

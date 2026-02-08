import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.repositories.evaluation import EvaluationsRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.evaluation import evaluation_db_schema_factory


@pytest.fixture
def repo() -> EvaluationsRepository:
    """EvaluationsRepository instance for testing custom methods."""
    return EvaluationsRepository()


@pytest.mark.anyio
async def test_get_many_by_app_id_filters_by_app_id_and_type(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    app2 = await app_db_schema_factory(db_conn)
    # matching app_id and type
    await evaluation_db_schema_factory(
        db_conn=db_conn,
        app_id=app.id,
        type=EvaluationType.LLM_ONLY,
    )
    # matching app_id and type
    await evaluation_db_schema_factory(
        db_conn=db_conn,
        app_id=app.id,
        type=EvaluationType.LLM_ONLY,
    )
    # matching app_id but wrong type
    await evaluation_db_schema_factory(
        db_conn=db_conn,
        app_id=app.id,
        type=EvaluationType.HUMAN_AND_LLM,
    )
    # matching type but wrong app_id
    await evaluation_db_schema_factory(
        db_conn=db_conn,
        app_id=app2.id,
        type=EvaluationType.LLM_ONLY,
    )
    # Act
    results = await repo.get_many_by_app_id(
        db_conn, app.id, EvaluationType.LLM_ONLY
    )

    # Assert
    assert len(results) == 2
    assert all(r.app_id == app.id for r in results)
    assert all(r.type == EvaluationType.LLM_ONLY for r in results)

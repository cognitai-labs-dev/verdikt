import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.sample import SamplesRepository
from tests.factories.evaluation import evaluation_db_schema_factory
from tests.factories.sample import sample_db_schema_factory


@pytest.fixture
def repo() -> SamplesRepository:
    """SamplesRepository instance for testing custom methods."""
    return SamplesRepository()


@pytest.mark.anyio
async def test_get_many_by_evaluation_returns_samples_for_given_evaluation_ids(
    db_conn: AsyncConnection, repo: SamplesRepository
):
    # Arrange
    eval_1 = await evaluation_db_schema_factory(db_conn=db_conn)
    eval_2 = await evaluation_db_schema_factory(db_conn=db_conn)
    eval_3 = await evaluation_db_schema_factory(db_conn=db_conn)

    await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_1.id
    )
    await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_1.id
    )
    await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_2.id
    )
    await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_3.id
    )

    # Act
    results = await repo.get_many_by_evaluation(
        db_conn, [eval_1.id, eval_2.id]
    )

    # Assert
    assert len(results) == 3
    returned_eval_ids = {r.evaluation_id for r in results}
    assert returned_eval_ids == {eval_1.id, eval_2.id}


@pytest.mark.anyio
async def test_get_many_by_evaluation_returns_empty_list_when_no_match(
    db_conn: AsyncConnection, repo: SamplesRepository
):
    # Act
    results = await repo.get_many_by_evaluation(db_conn, [999999])

    # Assert
    assert results == []

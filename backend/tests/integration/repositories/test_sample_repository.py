import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentType
from src.repositories.sample import SamplesRepository
from src.schemas.sample import SampleJudgmentSummarySchema
from tests.factories.app import app_db_schema_factory
from tests.factories.evaluation import evaluation_db_schema_factory
from tests.factories.judgment import judgment_db_schema_factory
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
    app = await app_db_schema_factory(db_conn)
    eval_1 = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    eval_2 = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    eval_3 = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )

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


@pytest.mark.anyio
async def test_get_many_by_evaluation_with_judgements_returns_flat_rows(
    db_conn: AsyncConnection, repo: SamplesRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    evaluation = await evaluation_db_schema_factory(
        db_conn=db_conn,
        app_id=app.id,
    )
    sample = await sample_db_schema_factory(
        db_conn=db_conn,
        evaluation_id=evaluation.id,
    )
    judgment = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample.id,
        judgment_type=JudgmentType.LLM,
    )
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample.id,
        judgment_type=JudgmentType.HUMAN,
    )

    # Act
    results = await repo.get_many_by_evaluation_with_judgements(
        db_conn,
        evaluation_id=evaluation.id,
        judgement_type=JudgmentType.LLM,
    )

    # Assert
    assert len(results) == 1
    row = results[0]
    assert isinstance(row, SampleJudgmentSummarySchema)
    assert row.sample_id == sample.id
    assert row.status == judgment.status
    assert row.passed == judgment.passed

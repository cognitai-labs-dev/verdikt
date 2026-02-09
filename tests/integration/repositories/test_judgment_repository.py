import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentStatus, JudgmentType
from src.repositories.judgment import JudgmentRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.evaluation import evaluation_db_schema_factory
from tests.factories.judgment import judgment_db_schema_factory
from tests.factories.prompt_version import (
    prompt_version_db_schema_factory,
)
from tests.factories.prompt_version import (
    prompt_version_db_schema_factory,
)
from tests.factories.sample import sample_db_schema_factory


@pytest.fixture
def repo() -> JudgmentRepository:
    """JudgmentRepository instance for testing custom methods."""
    return JudgmentRepository()


@pytest.fixture
async def sample_id(db_conn: AsyncConnection) -> int:
    """A persisted sample with its parent evaluation, returns the sample id."""
    app = await app_db_schema_factory(db_conn)
    evaluation = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    sample = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=evaluation.id
    )
    return sample.id


@pytest.mark.anyio
async def test_get_many_pending_returns_pending_llm_judgments_up_to_limit(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
    sample_id: int,
):
    # Arrange
    # matching status and type
    j1 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.LLM,
        status=JudgmentStatus.PENDING,
    )
    # matching status and type
    j2 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.LLM,
        status=JudgmentStatus.PENDING,
    )
    # matching status and type (over limit)
    j3 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.LLM,
        status=JudgmentStatus.PENDING,
    )
    # matching type but wrong status
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.LLM,
        status=JudgmentStatus.COMPLETED,
    )
    # matching status but wrong type
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.HUMAN,
        status=JudgmentStatus.PENDING,
    )

    # Act
    results = await repo.get_many_pending(db_conn, limit=2)

    # Assert
    result_ids = {r.id for r in results}
    assert len(results) == 2
    assert result_ids <= {j1.id, j2.id, j3.id}


@pytest.mark.anyio
async def test_get_many_pending_returns_empty_list_when_none_pending(
    db_conn: AsyncConnection, repo: JudgmentRepository
):
    # Act
    results = await repo.get_many_pending(db_conn, limit=10)

    # Assert
    assert results == []


@pytest.mark.anyio
async def test_get_many_by_prompt_ids_groups_by_sample_id(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
    sample_id: int,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    p = await prompt_version_db_schema_factory(
        db_conn, app_id=app.id
    )
    j1 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        prompt_version_id=p.id,
    )
    # non-matching prompt — should be excluded
    await judgment_db_schema_factory(
        db_conn=db_conn, sample_id=sample_id,
    )

    # Act
    results = await repo.get_many_by_prompt_ids(
        db_conn, [p.id]
    )

    # Assert
    assert list(results.keys()) == [sample_id]
    assert [j.id for j in results[sample_id]] == [j1.id]


@pytest.mark.anyio
async def test_get_many_by_prompt_ids_empty_input(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
):
    assert await repo.get_many_by_prompt_ids(db_conn, []) == {}


@pytest.mark.anyio
async def test_get_many_by_sample_ids_returns_judgments_grouped_by_sample_id_and_type(
    db_conn: AsyncConnection, repo: JudgmentRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    eval = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    s1 = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval.id
    )
    s2 = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval.id
    )
    # matching sample and type
    j1 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s1.id,
        judgment_type=JudgmentType.LLM,
    )
    # matching sample and type
    j2 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s1.id,
        judgment_type=JudgmentType.LLM,
    )
    # matching sample but wrong type
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s1.id,
        judgment_type=JudgmentType.HUMAN,
    )
    # matching type but different sample
    j3 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s2.id,
        judgment_type=JudgmentType.LLM,
    )

    # Act
    results = await repo.get_many_by_sample_ids(
        db_conn, [s1.id, s2.id], JudgmentType.LLM
    )

    # Assert
    assert results.keys() == {s1.id, s2.id}
    assert {j.id for j in results[s1.id]} == {j1.id, j2.id}
    assert [j.id for j in results[s2.id]] == [j3.id]


# --- get_human_judgments_by_sample_ids ---


@pytest.mark.anyio
async def test_get_human_judgments_by_sample_ids_returns_judgment_or_none_per_sample(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
    sample_id: int,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    eval = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    sample_without = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval.id
    )
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.HUMAN,
    )

    # Act
    results = await repo.get_human_judgments_by_sample_ids(
        db_conn, [sample_id, sample_without.id]
    )

    # Assert
    assert results.keys() == {sample_id, sample_without.id}
    assert results[sample_id] is not None
    assert results[sample_without.id] is None


@pytest.mark.anyio
async def test_get_llm_judgments_by_sample_id_returns_list_or_empty(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    eval_ = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    s1 = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_.id
    )
    s2 = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=eval_.id
    )
    j1 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s1.id,
        judgment_type=JudgmentType.LLM,
    )
    await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=s2.id,
        judgment_type=JudgmentType.LLM,
    )

    # Act
    results = await repo.get_llm_judgmenets_by_sample_id(
        db_conn, s1.id
    )

    # Assert
    assert len(results) == 1
    assert results[0].id == j1.id


# --- get_human_judgement_by_sample_id ---


@pytest.mark.anyio
async def test_get_human_judgement_by_sample_id_returns_judgment_or_none(
    db_conn: AsyncConnection,
    repo: JudgmentRepository,
    sample_id: int,
):
    # Arrange
    j1 = await judgment_db_schema_factory(
        db_conn=db_conn,
        sample_id=sample_id,
        judgment_type=JudgmentType.HUMAN,
    )

    # Act
    result = await repo.get_human_judgement_by_sample_id(
        db_conn, sample_id
    )

    # Assert
    assert result is not None
    assert result.id == j1.id

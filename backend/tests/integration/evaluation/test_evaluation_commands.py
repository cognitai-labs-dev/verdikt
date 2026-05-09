import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.evaluation.commands import EvaluationCommands
from src.evaluation.schemas import AppAnswerSchema, EvaluationSchema
from src.repositories.app_dataset import AppDatasetRepository
from src.repositories.apps import AppsRepository
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.sample import SamplesRepository
from src.schemas.app import AppUpdateSchema
from tests.factories.app import app_db_schema_factory
from tests.factories.app_dataset import app_dataset_db_schema_factory
from tests.factories.prompt_version import (
    prompt_version_db_schema_factory,
)


@pytest.fixture
def commands() -> EvaluationCommands:
    return EvaluationCommands(
        evaluation_repo=EvaluationsRepository(),
        sample_repo=SamplesRepository(),
        judgment_repo=JudgmentRepository(),
        app_dataset_repo=AppDatasetRepository(),
        app_repo=AppsRepository(),
    )


async def _seed_app_with_two_datasets(db_conn: AsyncConnection):
    app = await app_db_schema_factory(db_conn)
    prompt = await prompt_version_db_schema_factory(
        db_conn, app_id=app.id
    )
    await AppsRepository().update(
        db_conn,
        AppUpdateSchema(id=app.id, current_prompt_version_id=prompt.id),
    )
    ds_1 = await app_dataset_db_schema_factory(
        db_conn, app_id=app.id, question="Q1", human_answer="A1"
    )
    ds_2 = await app_dataset_db_schema_factory(
        db_conn, app_id=app.id, question="Q2", human_answer="A2"
    )
    return app, [ds_1, ds_2]


@pytest.mark.anyio
async def test_create_persists_app_cost_per_sample(
    db_conn: AsyncConnection, commands: EvaluationCommands
):
    # Arrange
    app, datasets = await _seed_app_with_two_datasets(db_conn)
    sample_repo = SamplesRepository()
    eval_repo = EvaluationsRepository()

    # Act
    await commands.create(
        db_conn,
        EvaluationSchema(
            app_id=app.id,
            app_version="1.0.0",
            evaluation_type=EvaluationType.LLM_ONLY,
            app_answers={
                datasets[0].id: AppAnswerSchema(
                    answer="ans1", cost=0.0125
                ),
                datasets[1].id: AppAnswerSchema(
                    answer="ans2", cost=0.7
                ),
            },
            llm_judge_models=[],
        ),
    )

    # Assert
    evaluations = await eval_repo.get_many_by_app_id(
        db_conn, app.id, EvaluationType.LLM_ONLY
    )
    assert len(evaluations) == 1
    samples = await sample_repo.get_many_by_evaluation(
        db_conn, [evaluations[0].id]
    )
    cost_by_question = {s.question: s.app_cost for s in samples}
    assert cost_by_question == {"Q1": 0.0125, "Q2": 0.7}


@pytest.mark.anyio
async def test_create_accepts_omitted_cost_and_stores_null(
    db_conn: AsyncConnection, commands: EvaluationCommands
):
    # Arrange
    app, datasets = await _seed_app_with_two_datasets(db_conn)
    sample_repo = SamplesRepository()
    eval_repo = EvaluationsRepository()

    # Act
    await commands.create(
        db_conn,
        EvaluationSchema(
            app_id=app.id,
            app_version="1.0.0",
            evaluation_type=EvaluationType.LLM_ONLY,
            app_answers={
                datasets[0].id: AppAnswerSchema(answer="ans1"),
                datasets[1].id: AppAnswerSchema(
                    answer="ans2", cost=None
                ),
            },
            llm_judge_models=[],
        ),
    )

    # Assert
    evaluations = await eval_repo.get_many_by_app_id(
        db_conn, app.id, EvaluationType.LLM_ONLY
    )
    samples = await sample_repo.get_many_by_evaluation(
        db_conn, [evaluations[0].id]
    )
    assert len(samples) == 2
    assert all(s.app_cost is None for s in samples)

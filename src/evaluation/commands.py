import logging

from sqlalchemy.ext.asyncio import AsyncConnection
from yalc import LLMModel

from src.constants import (
    EvaluationType,
    JudgmentStatus,
    JudgmentType,
)
from src.evaluation.schemas import EvaluationSchema
from src.repositories.app_dataset import AppDatasetRepository
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.sample import SamplesRepository
from src.schemas.evaluation import EvaluationCreateSchema
from src.schemas.judgment import JudgmentCreateSchema
from src.schemas.sample import (
    SampleCreateSchema,
    SampleSchema,
)


class EvaluationCommands:
    def __init__(
        self,
        evaluation_repo: EvaluationsRepository,
        sample_repo: SamplesRepository,
        judgment_repo: JudgmentRepository,
        app_dataset_repo: AppDatasetRepository,
    ):
        # TODO: fix later with passing models via request
        self.evaluation = evaluation_repo
        self.sample = sample_repo
        self.judgment = judgment_repo
        self.app_dataset = app_dataset_repo

        self.logger = logging.getLogger(__name__)

    async def create(
        self, conn: AsyncConnection, evaluation: EvaluationSchema
    ):
        self.logger.info(
            "Creating evaluation for %s", evaluation.app_id
        )

        datasets = await self.app_dataset.get_many_by_app_id(
            conn, evaluation.app_id
        )
        if not datasets:
            raise ValueError(
                f"No datasets found for app {evaluation.app_id}"
            )

        missing = [
            d.id
            for d in datasets
            if d.id not in evaluation.app_answers
        ]
        if missing:
            raise ValueError(
                f"Missing app answers for dataset IDs: {missing}"
            )

        eval_create = EvaluationCreateSchema(
            app_id=evaluation.app_id,
            type=evaluation.evaluation_type,
            version=evaluation.app_version,
        )
        created_evaluation = await self.evaluation.create(
            conn, eval_create
        )

        samples = [
            SampleCreateSchema(
                evaluation_id=created_evaluation.id,
                question=dataset.question,
                human_answer=dataset.human_answer,
                app_answer=evaluation.app_answers[dataset.id],
            )
            for dataset in datasets
        ]
        db_samples = await self.sample.create_many(conn, samples)

        await self._create_judgments(
            conn,
            db_samples,
            evaluation.evaluation_type,
            evaluation.llm_judge_models,
        )

    async def _create_judgments(
        self,
        conn: AsyncConnection,
        db_samples: list[SampleSchema],
        eval_type: EvaluationType,
        llm_judges: list[LLMModel],
    ):
        llm_judgments = []
        human_judgments = []
        for sample in db_samples:
            for model in llm_judges:
                llm_judgments.append(
                    JudgmentCreateSchema(
                        sample_id=sample.id,
                        judgment_model=model,
                        judgment_type=JudgmentType.LLM,
                        status=JudgmentStatus.PENDING,
                    )
                )
            if eval_type == eval_type.HUMAN_AND_LLM:
                human_judgments.append(
                    JudgmentCreateSchema(
                        sample_id=sample.id,
                        judgment_model="human",
                        judgment_type=JudgmentType.HUMAN,
                        status=JudgmentStatus.PENDING,
                    )
                )

        await self.judgment.create_many(conn, llm_judgments)
        await self.judgment.create_many(conn, human_judgments)

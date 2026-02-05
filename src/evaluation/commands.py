import logging

from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.schemas import EvaluationApiSchema
from src.config import Settings
from src.constants import (
    EvaluationType,
    JudgmentStatus,
    JudgmentType,
)
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
    ):
        # TODO: fix later with passing models via request
        self.llm_judges = Settings().JUDGING_LLM_MODELS
        self.evaluation = evaluation_repo
        self.sample = sample_repo
        self.judgment = judgment_repo

        self.logger = logging.getLogger(__name__)

    async def create(
        self, conn: AsyncConnection, request: EvaluationApiSchema
    ):
        self.logger.info("Creating evaluation for %s", request.app_id)
        evaluation = EvaluationCreateSchema(**request.model_dump())
        created_evaluation = await self.evaluation.create(
            conn, evaluation
        )

        samples = [
            SampleCreateSchema(
                evaluation_id=created_evaluation.id,
                **s.model_dump(),
            )
            for s in request.samples
        ]
        db_samples = await self.sample.create_many(conn, samples)

        await self._create_judgments(conn, db_samples, request.type)

    async def _create_judgments(
        self,
        conn: AsyncConnection,
        db_samples: list[SampleSchema],
        eval_type: EvaluationType,
    ):
        llm_judgments = []
        human_judgments = []
        for sample in db_samples:
            for model in self.llm_judges:
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

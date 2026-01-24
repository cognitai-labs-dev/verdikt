import logging

from src.api.schemas import EvaluationApiSchema
from src.config import settings
from src.constants import JudgmentType, JudgmentStatus
from src.crud.sample import samples_crud
from src.crud.evaluation import evaluations_crud
from src.crud.judgment import judgment_crud
from src.schemas.sample import SampleCreateSchema, SampleSchema
from src.schemas.evaluation import EvaluationCreateSchema
from src.schemas.judgment import JudgmentCreateSchema


class EvaluationService:
    def __init__(self):
        self.llm_judges = settings.JUDGING_LLM_MODELS
        self.logger = logging.getLogger(__name__)

    def create(self, request: EvaluationApiSchema):
        self.logger.info("Creating evaluation for %s", request.app_id)
        evaluation = EvaluationCreateSchema(**request.model_dump())
        created_evaluation = evaluations_crud.create(evaluation)

        samples = [
            SampleCreateSchema(evaluation_id=created_evaluation.id, **s.model_dump())
            for s in request.samples
        ]
        db_samples = samples_crud.create_many(samples)

        # Future improvement create many
        self._create_llm_judging(db_samples)

    def _create_llm_judging(self, db_samples: list[SampleSchema]):
        llm_judgments = []
        human_judgments = []
        for provider, model in self.llm_judges:
            for sample in db_samples:
                llm_judgments.append(
                    JudgmentCreateSchema(
                        sample_id=sample.id,
                        judgment_model=model,
                        judgment_type=JudgmentType.LLM,
                        status=JudgmentStatus.PENDING,
                    )
                )
                human_judgments.append(
                    JudgmentCreateSchema(
                        sample_id=sample.id,
                        judgment_model="human",
                        judgment_type=JudgmentType.HUMAN,
                        status=JudgmentStatus.PENDING,
                    )
                )

        judgment_crud.create_many(llm_judgments)
        judgment_crud.create_many(human_judgments)

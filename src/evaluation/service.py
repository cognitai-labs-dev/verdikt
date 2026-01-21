import logging

from src.api.schemas import EvaluationRunApiSchema
from src.config import settings
from src.constants import JudgeType, JudgeStatus
from src.crud.evaluation import evaluations_crud
from src.crud.evaluation_run import evaluation_runs_crud
from src.crud.judge import judge_crud
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema
from src.schemas.evaluation_run import EvaluationRunCreateSchema
from src.schemas.judge import JudgeCreateSchema


class EvaluationService:
    def __init__(self):
        self.llm_judges = settings.JUDGING_LLM_MODELS
        self.logger = logging.getLogger(__name__)

    def create(self, request: EvaluationRunApiSchema):
        self.logger.info("Creating evaluation for %s", request.app_id)
        run = EvaluationRunCreateSchema(**request.model_dump())
        created_run = evaluation_runs_crud.create(run)

        evals = [
            EvaluationCreateSchema(run_id=created_run.id, **e.model_dump())
            for e in request.evaluations
        ]
        db_evals = evaluations_crud.create_many(evals)

        # Future improvement create many
        self._create_llm_judging(db_evals)

    def _create_llm_judging(self, db_evals: list[EvaluationSchema]):
        llm_judges = []
        human_judges = []
        for provider, model in self.llm_judges:
            for evaluation in db_evals:
                llm_judges.append(
                    JudgeCreateSchema(
                        evaluation_id=evaluation.id,
                        judge_model=model,
                        judge_type=JudgeType.LLM,
                        status=JudgeStatus.PENDING,
                    )
                )
                human_judges.append(
                    JudgeCreateSchema(
                        evaluation_id=evaluation.id,
                        judge_model="human",
                        judge_type=JudgeType.HUMAN,
                        status=JudgeStatus.PENDING,
                    )
                )

        judge_crud.create_many(llm_judges)
        judge_crud.create_many(human_judges)

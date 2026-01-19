import logging

from src.api.schemas import EvaluationRunApiSchema
from src.config import settings
from src.constants import JudgeType, JudgeStatus
from src.crud.evaluation import evaluations_crud
from src.crud.evaluation_run import evaluation_runs_crud
from src.crud.judge_result import judge_results_crud
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema
from src.schemas.evaluation_run import EvaluationRunCreateSchema
from src.schemas.judge_result import JudgeResultCreateSchema


class EvaluationService:
    def __init__(self):
        self.llm_judges = settings.JUDGING_LLM_MODELS
        self.logger = logging.getLogger(__name__)

    def create(self, request: EvaluationRunApiSchema):
        self.logger.info("Creating evaluation for %s", request.app_id)
        run = EvaluationRunCreateSchema(**request.model_dump())
        run_id = evaluation_runs_crud.create(run)

        evals = [
            EvaluationCreateSchema(run_id=run_id, **e.model_dump())
            for e in request.evaluations
        ]
        db_evals = evaluations_crud.create_many(evals)

        # Future improvement create many
        self._create_llm_judging(db_evals)
        self._create_human_judging(db_evals)

    def _create_llm_judging(self, db_evals: list[EvaluationSchema]):
        for provider, model in self.llm_judges:
            self.logger.info("Using %s | %s judge", provider, model)
            for evaluation in db_evals:
                judge_result = JudgeResultCreateSchema(
                    evaluation_id=evaluation.id,
                    judge_model=model,
                    judge_type=JudgeType.LLM,
                    status=JudgeStatus.PENDING,
                )
                judge_results_crud.create(judge_result)

    @staticmethod
    def _create_human_judging(db_evals: list[EvaluationSchema]):
        for evaluation in db_evals:
            judge_result = JudgeResultCreateSchema(
                evaluation_id=evaluation.id,
                judge_model="human",
                judge_type=JudgeType.HUMAN,
                status=JudgeStatus.PENDING,
            )
            judge_results_crud.create(judge_result)

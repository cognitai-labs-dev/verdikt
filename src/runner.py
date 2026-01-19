import logging

from src.api.schemas import EvaluationRunApiSchema
from src.crud import evaluation_runs_crud, evaluations_crud, judge_results_crud
from src.juding.human import HumanJudge
from src.juding.openai import OpenAiJudge
from src.schemas import (
    EvaluationRunCreateSchema,
    EvaluationCreateSchema,
    JudgeResultCreateSchema,
)


class EvaluationRunner:
    def __init__(self):
        self.judges = [OpenAiJudge(), HumanJudge()]
        self.logger = logging.getLogger(__name__)

    def run(self, request: EvaluationRunApiSchema):
        self.logger.info("Running %s", request.app_id)
        run = EvaluationRunCreateSchema(**request.model_dump())
        run_id = evaluation_runs_crud.create(run)

        evals = [
            EvaluationCreateSchema(run_id=run_id, **e.model_dump())
            for e in request.evaluations
        ]
        db_evals = evaluations_crud.create_many(evals)

        for judge in self.judges:
            self.logger.info("Running %s judge", judge.model)
            for evaluation in db_evals:
                result = judge.judge(evaluation.question, evaluation.answer)
                judge_result = JudgeResultCreateSchema(
                    **result.model_dump(),
                    evaluation_id=evaluation.id,
                    judge_model=judge.model,
                    judge_type=judge.type,
                    input_tokens=None,
                    output_tokens_cost=None,
                    output_tokens=None,
                    input_tokens_cost=None,
                )
                judge_results_crud.create(judge_result)

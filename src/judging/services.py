from src.constants import JudgmentStatus, JudgmentType
from src.crud.sample import samples_crud
from src.crud.judgment import judgment_crud
from src.judging.schemas import JudgmentResult, PricingSchema, SampleSummary
from src.schemas.judgment import JudgmentUpdateSchema, JudgmentSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_crud

        self.sample = samples_crud

    def sample_judgments_summary(self, evaluation_id: int) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_id)
        sample_ids = {s.id: s for s in samples}
        human_judgments = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.HUMAN
        )
        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.LLM
        )

        sample_responses = []
        for sample_id, sample in sample_ids.items():
            human_judgment = human_judgments.get(sample_id)
            llm_judgments = llm_judgments_map.get(sample_id)

            sample_responses.append(
                SampleSummary(
                    **sample.model_dump(),
                    human_judgment_passed=human_judgment[0].passed
                    if len(human_judgment) == 1
                    else None,
                    llm_judgments_count=len(llm_judgments),
                    llm_judgments_count_passed=len(
                        [judgement for judgement in llm_judgments if judgement.passed]
                    ),
                ),
            )

        return sample_responses

    def get_human_judgment_by_sample(self, sample_id: int) -> JudgmentSchema | None:
        results = self.judgment.get_many_by_sample_id(sample_id, JudgmentType.HUMAN)
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise RuntimeError("More than 1 human judgment for a sample")

        return results[0]

    @staticmethod
    def save_judgment(
        judgment_id: int, result: JudgmentResult, pricing: PricingSchema | None = None
    ):
        update_schema = JudgmentUpdateSchema(
            id=judgment_id, status=JudgmentStatus.COMPLETED
        )

        update_schema.score = result.score
        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        if pricing:
            update_schema.input_tokens = pricing.input_tokens
            update_schema.output_tokens = pricing.output_tokens
            update_schema.input_tokens_cost = pricing.output_tokens_cost
            update_schema.output_tokens_cost = pricing.output_tokens_cost

        judgment_crud.update(update_schema)

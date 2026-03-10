from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.schemas import SampleJudgments, SampleSummary
from src.constants import (
    EvaluationType,
    JudgmentType,
)
from src.judgment.queries import JudgmentQueries
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.sample import SamplesRepository
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class SampleQueries:
    def __init__(
        self,
        judgment_repo: JudgmentRepository,
        sample_repo: SamplesRepository,
        evaluation_repo: EvaluationsRepository,
        judgment_queries: JudgmentQueries,
    ):
        self.judgment = judgment_repo
        self.sample = sample_repo
        self.evaluation = evaluation_repo
        self.judgment_queries = judgment_queries

    async def summary(
        self,
        conn: AsyncConnection,
        samples: list[SampleSchema],
        evaluation_type: EvaluationType,
    ) -> list[SampleSummary]:
        """
        Core method for calculating statistics for sample/judgment pairs
        This will get called multiple times for the same sample, for perf
        optimalization add caching by sample_id -> sample_summary
        """
        if len(samples) == 0:
            return []

        samples_mapped = {sample.id: sample for sample in samples}
        sample_ids = list(samples_mapped.keys())

        llm_judgments_map = (
            await self.judgment.get_many_by_sample_ids(
                conn, sample_ids, JudgmentType.LLM
            )
        )
        human_judgments_map = (
            await self.judgment.get_human_judgments_by_sample_ids(
                conn, sample_ids
            )
            if evaluation_type == EvaluationType.HUMAN_AND_LLM
            else {}
        )

        sample_responses = []
        for sample_id, sample in samples_mapped.items():
            llm_judgments = llm_judgments_map.get(sample_id, [])
            human_judgment = human_judgments_map.get(sample_id)

            sample_responses.append(
                self._sample_summary(
                    sample,
                    llm_judgments,
                    human_judgment,
                    evaluation_type,
                )
            )

        return sample_responses

    async def summary_by_eval_ids(
        self,
        conn: AsyncConnection,
        evaluation_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = await self.sample.get_many_by_evaluation(
            conn, evaluation_ids
        )
        return await self.summary(conn, samples, eval_type)

    async def summary_by_sample_ids(
        self,
        conn: AsyncConnection,
        sample_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = await self.sample.get_by_many_ids(conn, sample_ids)
        return await self.summary(conn, samples, eval_type)

    async def judgments_with_summary(
        self, conn: AsyncConnection, sample_id: int
    ) -> SampleJudgments | None:
        sample = await self.sample.get(conn, sample_id)
        if sample is None:
            return None

        evaluation = await self.evaluation.get(
            conn, sample.evaluation_id
        )
        if evaluation is None:
            return None

        summary = await self.summary(conn, [sample], evaluation.type)
        if len(summary) == 0:
            return None

        human_judgment = (
            await self.judgment.get_human_judgment_by_sample_id(
                conn, sample_id
            )
        )
        llm_judgments = (
            await self.judgment.get_llm_judgments_by_sample_id(
                conn, sample_id
            )
        )

        return SampleJudgments(
            **summary[0].model_dump(),
            human_judgment=human_judgment,
            llm_judgments=llm_judgments,
        )

    def _human_passed_count(
        self,
        evaluation_type: EvaluationType,
        summaries: list[SampleSummary],
    ) -> tuple[int, int]:
        human_judgments_count = 0
        human_judgments_completed = 0
        if evaluation_type == EvaluationType.HUMAN_AND_LLM:
            human_judgments_count = len(summaries)
            human_judgments_completed = sum(
                [
                    1
                    for summary in summaries
                    if summary.human_judgment_passed is not None
                ]
            )

        return human_judgments_count, human_judgments_completed

    def _sample_summary(
        self,
        sample: SampleSchema,
        llm_judgments: list[JudgmentSchema],
        human_judgment: JudgmentSchema | None,
        evaluation_type: EvaluationType,
    ) -> SampleSummary:
        """
        Create a sample summary from the judgments
        """
        total_cost = self.judgment_queries.llm_cost(llm_judgments) + (
            sample.app_cost or 0
        )
        human_passed = (
            human_judgment.passed if human_judgment else None
        )

        return SampleSummary(
            **sample.model_dump(),
            evaluation_type=evaluation_type,
            human_judgment_passed=human_passed,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=self.judgment_queries.pass_count(
                evaluation_type, llm_judgments, human_judgment
            ),
            llm_judgments_count_completed=self.judgment_queries.llm_completion_count(
                llm_judgments
            ),
            total_cost=total_cost,
        )

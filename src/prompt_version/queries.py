from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.schemas import PromptVersionSummary
from src.constants import EvaluationType
from src.prompt_version.schemas import PromptSummary
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.prompt_version import (
    PromptVersionRepository,
)
from src.sample.queries import SampleQueries


class PromptVersionQueries:
    def __init__(
        self,
        sample_queries: SampleQueries,
        prompt_version_repo: PromptVersionRepository,
        evaluation_repo: EvaluationsRepository,
    ):
        self.sample_queries = sample_queries
        self.prompt_version_repo = prompt_version_repo
        self.evaluation_repo = evaluation_repo

    async def prompts_summaries(
        self, conn: AsyncConnection, app_id: int
    ) -> list[PromptVersionSummary]:
        prompts = await self.prompt_version_repo.get_many_by_app_id(
            conn, app_id
        )

        prompt_hash_map = {p.id: p.hash for p in prompts}
        prompt_stats: dict[str, PromptSummary] = {
            p.hash: PromptSummary() for p in prompts
        }

        evals_by_prompt = (
            await self.evaluation_repo.get_many_by_prompt_version_ids(
                conn, list(prompt_hash_map.keys())
            )
        )

        for prompt_id, evaluations in evals_by_prompt.items():
            prompt_hash = prompt_hash_map[prompt_id]
            stats = prompt_stats[prompt_hash]

            for evaluation in evaluations:
                sample_summaries = (
                    await self.sample_queries.summary_by_eval_ids(
                        conn,
                        [evaluation.id],
                        evaluation.type,
                    )
                )
                for summary in sample_summaries:
                    if (
                        evaluation.type
                        == EvaluationType.HUMAN_AND_LLM
                    ):
                        stats.human_and_llm_total_count += (
                            summary.llm_judgments_count
                        )
                        stats.human_and_llm_matched_count += (
                            summary.llm_judgments_count_passed
                        )
                    else:
                        stats.llm_total_count += (
                            summary.llm_judgments_count
                        )
                        stats.llm_passed_count += (
                            summary.llm_judgments_count_passed
                        )

        return [
            PromptVersionSummary(
                **prompt.model_dump(),
                **prompt_stats[prompt.hash].model_dump(),
            )
            for prompt in prompts
        ]

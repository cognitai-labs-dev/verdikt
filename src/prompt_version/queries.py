from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.schemas import PromptVersionSummary
from src.constants import JudgmentType
from src.prompt_version.schemas import PromptSummary
from src.repositories.judgment import JudgmentRepository
from src.repositories.prompt_version import PromptVersionRepository
from src.sample.queries import SampleQueries


class PromptVersionQueries:
    def __init__(
        self,
        sample_queries: SampleQueries,
        prompt_version_repo: PromptVersionRepository,
        judgement_repo: JudgmentRepository,
    ):
        self.sample_queries = sample_queries
        self.prompt_version_repo = prompt_version_repo
        self.judgement_repo = judgement_repo

    async def prompts_summaries(
        self, conn: AsyncConnection, app_id: int
    ) -> list[PromptVersionSummary]:
        result = []

        # Get all prompts
        prompts = await self.prompt_version_repo.get_many_by_app_id(
            conn, app_id
        )
        prompt_stats: dict[str, PromptSummary] = {
            prompt.hash: PromptSummary() for prompt in prompts
        }

        prompt_ids = {prompt.id: prompt.hash for prompt in prompts}

        # Get prompt judgments
        judgements = await self.judgement_repo.get_many_by_prompt_ids(
            conn, list(prompt_ids.keys())
        )

        for judgement in judgements:
            prompt_hash = prompt_ids[judgement.prompt_version_id]
            if judgement.judgment_type == JudgmentType.LLM:
                prompt_stats[prompt_hash].llm_passed_count += (
                    1 if judgement.passed else 0
                )
                prompt_stats[prompt_hash].llm_total_count += 1

        return result

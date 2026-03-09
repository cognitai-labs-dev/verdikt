import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncEngine
from yalc import create_client, LLMModel

from src.config import ProcessorSettings
from src.dependencies import (
    db_adpater,
    evaluation_repo,
    judgement_commands,
    judgment_repo,
    prompt_version_repo,
    sample_repo,
)
from src.judgement.commands import JudgementCommands
from src.judgement.schemas import JudgmentResult, PricingSchema
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.prompt_version import PromptVersionRepository
from src.repositories.sample import SamplesRepository
from src.schemas.judgment import JudgmentSchema


class JudgmentProcessor:
    def __init__(
        self,
        db_engine: AsyncEngine,
        settings: ProcessorSettings,
        judgment_repo: JudgmentRepository,
        sample_repo: SamplesRepository,
        judgement_commands: JudgementCommands,
        prompt_version_repo: PromptVersionRepository,
        evaluation_repo: EvaluationsRepository,
    ):
        self.logger = logging.getLogger(__name__)
        self.db_engine = db_engine

        self.running = True

        self.batch_size = settings.WORKER_BATCH_SIZE
        self.wait_time = settings.WORKER_WAIT_TIME
        self.clients = {
            model: create_client(model)
            for model in settings.JUDGING_LLM_MODELS
        }

        self.judgment_repo = judgment_repo
        self.judgement_commands = judgement_commands
        self.sample_repo = sample_repo
        self.prompt_version_repo = prompt_version_repo
        self.evaluation_repo = evaluation_repo

    async def run(self):
        while self.running:
            async with self.db_engine.begin() as conn:
                pending_judgments = (
                    await self.judgment_repo.get_many_pending(
                        conn, self.batch_size
                    )
                )

            if len(pending_judgments) == 0:
                self.logger.info("No pending judgments, waiting...")
                await asyncio.sleep(self.wait_time)
                continue

            await self._process_judgments(pending_judgments)

    async def _process_judgments(
        self, judgments: list[JudgmentSchema]
    ):
        self.logger.info(
            "Processing pending judgments (%d)", len(judgments)
        )
        tasks = [
            self._process_one_judgment(judgment)
            for judgment in judgments
        ]
        await asyncio.gather(*tasks)
        self.logger.info(
            "Done processing pending judgments in a batch"
        )

    async def _process_one_judgment(self, judgement: JudgmentSchema):
        self.logger.info(
            "Processing judgment (%s) with id: %d",
            judgement.judgment_model,
            judgement.id,
        )

        client = self.clients[LLMModel(judgement.judgment_model)]
        async with self.db_engine.begin() as conn:
            sample = await self.sample_repo.get(
                conn, judgement.sample_id
            )
            if sample is None:
                raise RuntimeError("Sample not found for judgment")
            evaluation = await self.evaluation_repo.get(
                conn, sample.evaluation_id
            )
            if evaluation is None:
                raise RuntimeError(
                    "Evaluation not found for judgment"
                )
            prompt = await self.prompt_version_repo.get(
                conn, evaluation.prompt_version_id
            )

        if prompt is None:
            raise RuntimeError("Prompt not found for judgment")

        user_content = (
            f"Question:\n{sample.question}\n\n"
            f"Golden standard (human answer):\n"
            f"{sample.human_answer}\n\n"
            f"App answer:\n{sample.app_answer}"
        )
        messages = [
            {"role": "system", "content": prompt.content},
            {"role": "user", "content": user_content},
        ]

        result, metadata = await client.structured_response(
            JudgmentResult, messages
        )
        async with self.db_engine.begin() as conn:
            await self.judgement_commands.create(
                conn,
                judgement.id,
                result,
                PricingSchema(**metadata.model_dump()),
            )

        self.logger.info(
            "Done judgement (%s) with id: %d",
            judgement.judgment_model,
            judgement.id,
        )


async def main():
    settings = ProcessorSettings()
    await db_adpater.connect(settings.postgres_dsn)
    processor = JudgmentProcessor(
        db_adpater.engine,
        settings,
        judgment_repo,
        sample_repo,
        judgement_commands,
        prompt_version_repo,
        evaluation_repo,
    )
    await processor.run()

    await db_adpater.disconnect()

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncEngine
from yalc import LLMModel, create_client

from src.config import ProcessorSettings
from src.dependencies import (
    db_adpater,
    judgement_commands,
    judgment_repo,
    sample_repo,
)
from src.judgement.commands import JudgementCommands
from src.judgement.prompts import (
    JUDGE_SYSTEM_PROMPT,
)
from src.judgement.schemas import JudgmentResult, PricingSchema
from src.repositories.judgment import JudgmentRepository
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

    async def _process_one_judgment(self, judgment: JudgmentSchema):
        self.logger.info(
            "Processing judgment (%s) with id: %d",
            judgment.judgment_model,
            judgment.id,
        )

        client = self.clients[LLMModel(judgment.judgment_model)]
        async with self.db_engine.begin() as conn:
            sample = await self.sample_repo.get(
                conn, judgment.sample_id
            )
        if sample is None:
            raise RuntimeError("Sample not found for judgment")

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": sample.question},
            {"role": "user", "content": sample.human_answer},
            {"role": "assistant", "content": sample.app_answer},
        ]

        result, metadata = await client.structured_response(
            JudgmentResult, messages
        )
        async with self.db_engine.begin() as conn:
            await self.judgement_commands.create(
                conn,
                judgment.id,
                result,
                PricingSchema(**metadata.model_dump()),
            )

        self.logger.info(
            "Done judgement (%s) with id: %d",
            judgment.judgment_model,
            judgment.id,
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
    )
    await processor.run()

    await db_adpater.disconnect()

import asyncio
import logging

from llm import LLMModel, create_client
from src.config import settings
from src.judgement.commands import JudgementCommands
from src.judgement.prompts import (
    JUDGE_EVAL_PROMPT,
    JUDGE_SYSTEM_PROMPT,
)
from src.judgement.schemas import JudgmentResult, PricingSchema
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentSchema


class JudgmentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = True
        self.batch_size = settings.WORKER_BATCH_SIZE
        self.wait_time = settings.WORKER_WAIT_TIME
        self.clients = {
            model: create_client(model)
            for model in settings.JUDGING_LLM_MODELS
        }
        self.judgement_commands = JudgementCommands()

    async def run(self):
        while self.running:
            pending_judgments = judgment_repository.get_many_pending(
                self.batch_size
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
        sample = samples_repository.get(judgment.sample_id)
        if sample is None:
            raise RuntimeError("Sample not found for judgment")

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": sample.question},
            {"role": "user", "content": sample.human_answer},
            {"role": "assistant", "content": sample.app_answer},
            {"role": "user", "content": JUDGE_EVAL_PROMPT},
        ]

        result, metadata = await client.structured_response(
            JudgmentResult, messages
        )
        self.judgement_commands.save_judgment(
            judgment.id,
            result,
            PricingSchema(**metadata.model_dump()),
        )

        self.logger.info(
            "Done judgement (%s) with id: %d",
            judgment.judgment_model,
            judgment.id,
        )

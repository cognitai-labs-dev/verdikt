import asyncio
import logging

from llm import Client
from src.config import settings
from src.repositories.sample import samples_repository
from src.repositories.judgment import judgment_repository
from src.depedencies import async_instructor_client
from src.judging.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_EVAL_PROMPT
from src.judging.schemas import JudgmentResult, PricingSchema
from src.judging.services import JudgmentService
from src.schemas.judgment import JudgmentSchema


class JudgmentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = True
        self.batch_size = settings.WORKER_BATCH_SIZE
        self.wait_time = settings.WORKER_WAIT_TIME
        # Temporarily just used openai
        self.client = Client(
            [],
            async_instructor_client,
            settings.JUDGING_LLM_MODELS[0].model,
        )
        self.judging_service = JudgmentService()

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
            "Processing one judgment %s with id: %d",
            judgment.judgment_model,
            judgment.id,
        )

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

        result, metadata = await self.client.structured_response(
            JudgmentResult, messages
        )
        self.judging_service.save_judgment(
            judgment.id,
            result,
            PricingSchema(**metadata.model_dump()),
        )

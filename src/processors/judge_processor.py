import asyncio
import logging

from llm import Client
from src.config import settings
from src.crud.evaluation import evaluations_crud
from src.crud.judge import judge_crud
from src.depedencies import async_instructor_client
from src.judging.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_EVAL_PROMPT
from src.judging.schemas import JudgeResult, PricingSchema
from src.judging.services import JudgeService
from src.schemas.judge import JudgeSchema


class JudgeProcessor:
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
        self.judging_service = JudgeService()

    async def run(self):
        while self.running:
            pending_judges = judge_crud.get_many_pending(self.batch_size)
            if len(pending_judges) == 0:
                self.logger.info("No pending judges, waiting...")
                await asyncio.sleep(self.wait_time)
                continue

            await self._process_judges(pending_judges)

    async def _process_judges(self, judges: list[JudgeSchema]):
        self.logger.info("Processing pending judges (%d)", len(judges))
        tasks = [self._process_one_judge(judge) for judge in judges]
        await asyncio.gather(*tasks)
        self.logger.info("Done processing pending judges in a batch")

    async def _process_one_judge(self, judge: JudgeSchema):
        self.logger.info(
            "Processing one judge %s with id: %d", judge.judge_model, judge.id
        )

        evaluation = evaluations_crud.get(judge.evaluation_id)
        if evaluation is None:
            raise RuntimeError("Evaluation not found for judge")

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": evaluation.question},
            {"role": "assistant", "content": evaluation.answer},
            {"role": "user", "content": JUDGE_EVAL_PROMPT},
        ]

        result, metadata = await self.client.structured_response(
            JudgeResult, messages, None
        )
        self.judging_service.save_judge(
            judge.id, result, PricingSchema(**metadata.model_dump())
        )

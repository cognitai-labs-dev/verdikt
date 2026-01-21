import asyncio
import logging

from llm import Client
from src.config import settings
from src.constants import JudgeStatus
from src.crud.evaluation import evaluations_crud
from src.crud.judge import judge_crud
from src.depedencies import async_instructor_client
from src.judging.logging import JudgeClientLoggingStrategy
from src.judging.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_EVAL_PROMPT
from src.judging.schemas import JudgeResult
from src.schemas.judge import JudgeSchema, JudgeUpdateSchema


class JudgeProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = True
        self.batch_size = settings.WORKER_BATCH_SIZE
        self.wait_time = settings.WORKER_WAIT_TIME
        # Temporarily just used openai
        self.client = Client(
            [JudgeClientLoggingStrategy()],
            async_instructor_client,
            settings.JUDGING_LLM_MODELS[0].model,
        )

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

        update_schema = JudgeUpdateSchema(id=judge.id, status=JudgeStatus.COMPLETED)
        result = await self.client.structured_response(
            JudgeResult, messages, update_schema
        )
        update_schema.score = result.score
        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        judge_crud.update(update_schema)

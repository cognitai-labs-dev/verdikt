import logging
from asyncio import gather

from tenacity import sleep

from src.constants import JudgeStatus
from src.crud.judge import judge_crud
from src.schemas.judge import JudgeSchema, JudgeUpdateSchema


class JudgeProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = True
        self.batch_size = 2
        self.wait_time = 5

    async def run(self):
        while self.running:
            pending_judges = judge_crud.get_many_pending(self.batch_size)
            if len(pending_judges) == 0:
                self.logger.info("No pending judges, waiting...")
                sleep(self.wait_time)
                continue

            self.logger.info("Processing pending judges...")
            await self._process_judges(pending_judges)

    async def _process_judges(self, judges: list[JudgeSchema]):
        tasks = [self._process_one_judge(judge) for judge in judges]
        await gather(*tasks)
        self.logger.info("Done processing pending judges")

    async def _process_one_judge(self, judge: JudgeSchema):
        # TODO: Actually process
        judge_crud.update(
            JudgeUpdateSchema(id=judge.id, status=JudgeStatus.COMPLETED, passed=True)
        )

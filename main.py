import asyncio

from src.api.schemas import EvaluationRunApiSchema, EvaluationApiSchema
from src.evaluation.service import EvaluationService
from src.processors.judge_processor import JudgeProcessor
from src.logging import setup_logging

setup_logging()

import logging

import typer

logger = logging.getLogger(__name__)
app = typer.Typer(pretty_exceptions_enable=False)


def create_example_request() -> EvaluationRunApiSchema:
    return EvaluationRunApiSchema(
        app_id="ai-oncall-assistant",
        app_version="1.0.0",
        metadata={},
        evaluations=[
            EvaluationApiSchema(
                question="how do I remove a forgotten card",
                answer="""
                    1. Check card status: `[SQL: payments_recurrent] SELECT shop_id, status FROM payments_recurrent WHERE shop_id = {local_shop_id}`
                    2. Evaluate status of the card: If the status is `active`, investigate if there is another underlying issue; if `inactive`, prepare to update it to `token_deleted`.
                    3. Determine reason for inactivity if status is `inactive`: Verify if the shop turned it off, check for insufficient credit/card limits, or confirm if the card has expired - ⚠️ MISSING INFO: Documentation does not specify exact command or procedure to update status to `token_deleted`. 
                """,
                app_cost=0.05,
                metadata={},
            ),
            EvaluationApiSchema(
                question="what does the exit click service do",
                answer="""Routed to *one_exit* service but theres no agent for it. Please refer to the help of a human.""",
                app_cost=0.05,
                metadata={},
            ),
            EvaluationApiSchema(
                question="how is sameprice offer rank calculated",
                answer="""
                    The sameprice offer rank is calculated based on the formula: RankScore = (1 + A + B
                    + C + D + E) × 100. Here, A is the delivery price (0.5 if missing, otherwise 0),
                    B is the availability (with specific values for missing, in stock, or different
                    delivery times), C is the shop rating, D is buyability (10 if buyable at Heureka
                    Marketplace), and E is the shop certificate level.
                """,
                app_cost=0.05,
                metadata={},
            ),
        ],
    )


@app.command()
def evaluate():
    request = create_example_request()
    runner = EvaluationService()
    runner.create(request)


@app.command()
def run_judging():
    processor = JudgeProcessor()

    async def run():
        await processor.run()

    asyncio.run(run())


if __name__ == "__main__":
    app()

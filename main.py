import asyncio

import uvicorn

from src.api.schemas import EvaluationApiSchema, SampleApiSchema
from src.config import Settings
from src.constants import EvaluationType
from src.db.pg import db
from src.dependencies import evaluation_commands
from src.logging import setup_logging
from src.processors.judgment_processor import main as processor_main

setup_logging()

import logging

import typer

logger = logging.getLogger(__name__)
app = typer.Typer(pretty_exceptions_enable=False)


def create_example_request(
    eval_type: EvaluationType,
) -> EvaluationApiSchema:
    return EvaluationApiSchema(
        app_id="ai-oncall-assistant",
        app_version="1.0.0",
        metadata={},
        type=eval_type,
        samples=[
            SampleApiSchema(
                question="how do I remove a forgotten card",
                app_answer="""
                    1. Check card status: `[SQL: payments_recurrent] SELECT shop_id, status FROM 
                    payments_recurrent WHERE shop_id = {local_shop_id}`
                    2. Evaluate status of the card: If the status is `active`, investigate if 
                    there is another underlying issue; if `inactive`, prepare to update it to 
                    `token_deleted`.
                    3. Determine reason for inactivity if status is `inactive`: Verify if the 
                    shop turned it off, check for insufficient credit/card limits, or confirm if 
                    the card has expired - ⚠️ MISSING INFO: Documentation does not specify exact 
                    command or procedure to update status to `token_deleted`.
                """,
                human_answer="""
                    1. Check card status: `[SQL: payments_recurrent] SELECT shop_id, status FROM 
                    payments_recurrent WHERE shop_id = {local_shop_id}`
                    2. Evaluate status of the card: If the status is `active`, investigate if 
                    there is another underlying issue; if `inactive`, prepare to update it to 
                    `token_deleted`.
                    3. Determine reason for inactivity if status is `inactive`: Verify if the 
                    shop turned it off, check for insufficient credit/card limits, or confirm if 
                    the card has expired.
                    4. Update it with UPDATE payment_recurrent SET status = 'active'
                    5. Check the card status by running SELECT * FROM cards where shop_id={
                    local_shop_id}
                """,
                app_cost=0.0,
                metadata={},
            ),
            SampleApiSchema(
                question="what does the exit click service do",
                app_answer="""Routed to *one_exit* service but theres no agent for it. Please 
                refer to the help of a human.""",
                human_answer="""It forwards exits to the credit service and filters bots""",
                app_cost=0.00,
                metadata={},
            ),
            SampleApiSchema(
                question="how is sameprice offer rank calculated",
                app_answer="""
                    The sameprice offer rank is calculated based on the formula: RankScore = (1 + 
                    A + B
                    + C + D + E) × 100. Here, A is the delivery price (0.5 if missing, otherwise 0),
                    B is the availability (with specific values for missing, in stock, or different
                    delivery times), C is the shop rating, D is buyability (10 if buyable at Heureka
                    Marketplace), and E is the shop certificate level.
                """,
                human_answer="""
                    The sameprice offer rank is calculated based on the formula: RankScore = (1 + 
                    A + B
                    + C + D + E) × 100. Here, A is the delivery price (0.5 if missing, otherwise 0),
                    B is the availability (with specific values for missing, in stock, or different
                    delivery times), C is the shop rating, D is buyability (10 if buyable at Heureka
                    Marketplace), and E is the shop certificate level.
                """,
                app_cost=0.0,
                metadata={},
            ),
        ],
    )


@app.command()
def evaluate(eval_type: EvaluationType):
    async def run():
        request = create_example_request(eval_type)
        await db.connect(Settings().postgresql)

        async with db.engine.begin() as conn:
            await evaluation_commands.create(conn, request)

        await db.disconnect()

    asyncio.run(run())


@app.command()
def run_judging():
    async def run():
        await processor_main()

    asyncio.run(run())


@app.command()
def api():
    uvicorn.run(
        "src.api_app:api_factory",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    app()

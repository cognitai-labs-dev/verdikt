import asyncio
import os

import logging

import typer
import uvicorn
from verdikt_sdk import VerdiktClient, EvaluationType, Question
from yalc import LLMModel

from src.logging import setup_logging
from src.processors.judgment_processor import main as processor_main

setup_logging()

logger = logging.getLogger(__name__)
app = typer.Typer(pretty_exceptions_enable=False)

BASE_URL = "http://localhost:8000/v1"

DATASETS = [
    {
        "question": "how do I remove a forgotten card",
        "human_answer": """
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
        "app_answer": """
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
    },
    {
        "question": "what does the exit click service do",
        "human_answer": """It forwards exits to the credit service and filters bots""",
        "app_answer": """Routed to *one_exit* service but theres no agent for it. Please
            refer to the help of a human.""",
    },
    {
        "question": "how is sameprice offer rank calculated",
        "human_answer": """
            The sameprice offer rank is calculated based on the formula: RankScore = (1 +
            A + B
            + C + D + E) × 100. Here, A is the delivery price (0.5 if missing, otherwise 0),
            B is the availability (with specific values for missing, in stock, or different
            delivery times), C is the shop rating, D is buyability (10 if buyable at Heureka
            Marketplace), and E is the shop certificate level.
        """,
        "app_answer": """
            The sameprice offer rank is calculated based on the formula: RankScore = (1 +
            A + B
            + C + D + E) × 100. Here, A is the delivery price (0.5 if missing, otherwise 0),
            B is the availability (with specific values for missing, in stock, or different
            delivery times), C is the shop rating, D is buyability (10 if buyable at Heureka
            Marketplace), and E is the shop certificate level.
        """,
    },
]


@app.command()
def evaluate(
        eval_type: str = typer.Argument(
            default="HUMAN_AND_LLM", help="Evaluation type"
        ),
):
    """Create an evaluation using hardcoded app answers."""

    async def run():
        verdikt = VerdiktClient(
            "http://localhost:8000",
            client_id=os.environ["VERDIKT_CLIENT_ID"],
            client_secret=os.environ["VERDIKT_CLIENT_SECRET"],
        )

        questions = [
            Question(question=d["question"], human_answer=d["human_answer"])
            for d in DATASETS
        ]

        await verdikt.create_app("eval-app", "Evaluation")
        await verdikt.add_questions("eval-app", questions)

        app_answers = {d["question"]: d["app_answer"] for d in DATASETS}

        async def callback(question: str) -> str:
            return app_answers[question]

        await verdikt.run_evaluation(
            app_slug="eval-app",
            app_version="1.0.0",
            callback=callback,
            evaluation_type=EvaluationType(eval_type),
            llm_judge_models=[LLMModel.gpt_5_mini, LLMModel.gpt_4o_mini],
        )

        logger.info("Created %s evaluation", eval_type)

    asyncio.run(run())


@app.command()
def run_judging():
    """Process pending LLM judgments."""

    async def run():
        await processor_main()

    asyncio.run(run())


@app.command()
def api():
    """Start the FastAPI server."""
    uvicorn.run(
        "src.api_app:api_factory",
        host="0.0.0.0",
        factory=True,
        port=8000,
        reload=True,
        log_config=None,
    )


if __name__ == "__main__":
    app()

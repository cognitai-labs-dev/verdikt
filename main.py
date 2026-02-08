import asyncio
import logging

import httpx
import typer
import uvicorn

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
def create_app():
    """Create the ai-oncall-assistant application."""
    response = httpx.post(
        f"{BASE_URL}/app", json={"name": "ai-oncall-assistant"}
    )
    response.raise_for_status()
    logger.info("Created app 'ai-oncall-assistant'")


@app.command()
def create_datasets(
    app_id: int = typer.Argument(help="Application ID"),
):
    """Load hardcoded datasets for an application."""
    payload = {
        "datasets": [
            {
                "question": d["question"],
                "human_answer": d["human_answer"],
            }
            for d in DATASETS
        ]
    }
    response = httpx.post(
        f"{BASE_URL}/app/{app_id}/datasets", json=payload
    )
    response.raise_for_status()
    logger.info(
        "Created %d datasets for app_id=%d",
        len(DATASETS),
        app_id,
    )


@app.command()
def evaluate(
    app_id: int = typer.Argument(help="Application ID"),
    eval_type: str = typer.Argument(
        default="HUMAN_AND_LLM", help="Evaluation type"
    ),
):
    """Create an evaluation using hardcoded app answers."""
    datasets_by_question = {d["question"]: d for d in DATASETS}

    response = httpx.get(f"{BASE_URL}/app/{app_id}/datasets")
    response.raise_for_status()
    db_datasets = response.json()

    app_answers = {}
    for ds in db_datasets:
        if ds["question"] in datasets_by_question:
            app_answers[str(ds["id"])] = datasets_by_question[
                ds["question"]
            ]["app_answer"]

    payload = {
        "app_version": "1.0.0",
        "evaluation_type": eval_type,
        "app_answers": app_answers,
    }
    response = httpx.post(
        f"{BASE_URL}/app/{app_id}/evaluation", json=payload
    )
    response.raise_for_status()
    logger.info(
        "Created %s evaluation for app_id=%d",
        eval_type,
        app_id,
    )


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

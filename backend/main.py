import asyncio
import logging
import os

import typer
import uvicorn
from verdikt_sdk import (
    AnswerWithCost,
    EvaluationType,
    Question,
    VerdiktClient,
)
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
            Question(
                question=d["question"], human_answer=d["human_answer"]
            )
            for d in DATASETS
        ]

        await verdikt.create_app("eval-app", "Evaluation")
        await verdikt.add_questions("eval-app", questions, True)

        app_answers = {
            d["question"]: d["app_answer"] for d in DATASETS
        }

        async def callback(question: str) -> AnswerWithCost:
            return AnswerWithCost(
                answer=app_answers[question], cost=0.0
            )

        await verdikt.run_evaluation(
            app_slug="eval-app",
            app_version="1.0.0",
            callback=callback,
            evaluation_type=EvaluationType(eval_type),
            llm_judge_models=[
                LLMModel.gpt_5_mini,
                LLMModel.gpt_4o_mini,
            ],
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
def create_client(
    name: str = typer.Argument(..., help="Human-readable client label"),
    app_slug: str = typer.Option(
        None, "--app", help="Bind the client to a single app (by slug)"
    ),
    admin: bool = typer.Option(
        False, "--admin", help="Grant access to every app"
    ),
):
    """Create a machine client and print its credentials once."""

    async def run():
        from src.auth.commands import AuthCommands
        from src.config import APISettings
        from src.dependencies import (
            app_principal_repo,
            app_repo,
            db_adpater,
            machine_client_repo,
            machine_token_repo,
        )

        app_slugs = [app_slug] if app_slug else []

        settings = APISettings()
        await db_adpater.connect(settings.postgres_dsn)
        try:
            async with db_adpater.engine.begin() as conn:
                commands = AuthCommands(
                    machine_client_repo=machine_client_repo,
                    machine_token_repo=machine_token_repo,
                    token_ttl=settings.MACHINE_TOKEN_TTL,
                    app_repo=app_repo,
                    app_principal_repo=app_principal_repo,
                )
                try:
                    client, client_secret = (
                        await commands.create_machine_client(
                            conn,
                            name=name,
                            is_admin=admin,
                            app_slugs=app_slugs,
                        )
                    )
                except ValueError as exc:
                    raise typer.BadParameter(str(exc)) from exc
        finally:
            await db_adpater.disconnect()

        typer.echo(f"client_id={client.client_id}")
        typer.echo(f"client_secret={client_secret}")
        typer.echo("Store the secret now — it is not recoverable.")

    asyncio.run(run())


@app.command()
def add_member(
    app_slug: str = typer.Argument(..., help="App slug"),
    email: str = typer.Argument(..., help="Member email"),
):
    """Bind a human (by email) to an app."""

    async def run():
        from src.config import APISettings
        from src.constants import SubjectType
        from src.dependencies import (
            app_principal_repo,
            app_repo,
            db_adpater,
        )

        settings = APISettings()
        await db_adpater.connect(settings.postgres_dsn)
        try:
            async with db_adpater.engine.begin() as conn:
                app_row = await app_repo.get_by_slug(conn, app_slug)
                if app_row is None:
                    raise typer.BadParameter(
                        f"app '{app_slug}' not found"
                    )
                await app_principal_repo.add(
                    conn, app_row.id, SubjectType.EMAIL, email
                )
        finally:
            await db_adpater.disconnect()

        typer.echo(f"Bound {email} to app '{app_slug}'")

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

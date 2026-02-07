from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.pg import DBAdapter
from src.evaluation.commands import EvaluationCommands
from src.evaluation.queries import EvaluationQueries
from src.judgement.commands import JudgementCommands
from src.judgement.queries import JudgementQueries
from src.repositories.app_dataset import AppDatasetRepository
from src.repositories.apps import AppsRepository
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.sample import SamplesRepository
from src.sample.queries import SampleQueries


async def get_connection() -> AsyncIterator[AsyncConnection]:
    async with db_adpater.engine.connect() as conn:
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


# Repositories

evaluation_repo = EvaluationsRepository()
judgment_repo = JudgmentRepository()
sample_repo = SamplesRepository()
app_repo = AppsRepository()
app_dataset_repo = AppDatasetRepository()

# Queries

judgement_queries = JudgementQueries()
sample_queries = SampleQueries(
    judgment_repo=judgment_repo,
    sample_repo=sample_repo,
    evaluation_repo=evaluation_repo,
    judgement_queries=judgement_queries,
)
evaluation_queries = EvaluationQueries(
    sample_queries=sample_queries,
)

# Commands

judgement_commands = JudgementCommands(
    judgment_repo=judgment_repo,
)

evaluation_commands = EvaluationCommands(
    evaluation_repo=evaluation_repo,
    sample_repo=sample_repo,
    judgment_repo=judgment_repo,
    app_dataset_repo=app_dataset_repo,
)

db_adpater = DBAdapter()

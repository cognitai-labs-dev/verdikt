from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection

from src.app.commands import AppCommands
from src.app.queries import AppDatasetQueries
from src.db.pg import DBAdapter
from src.evaluation.commands import EvaluationCommands
from src.evaluation.queries import EvaluationQueries
from src.judgement.commands import JudgementCommands
from src.judgement.queries import JudgementQueries
from src.prompt_version.queries import PromptVersionQueries
from src.repositories.app_dataset import AppDatasetRepository
from src.repositories.apps import AppsRepository
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.prompt_version import (
    PromptVersionRepository,
)
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
prompt_version_repo = PromptVersionRepository()

# Queries

app_dataset_queries = AppDatasetQueries(
    app_dataset_repo=app_dataset_repo
)

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
prompt_queries = PromptVersionQueries(
    sample_queries=sample_queries,
    prompt_version_repo=prompt_version_repo,
    evaluation_repo=evaluation_repo,
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
    app_repo=app_repo,
)

app_commands = AppCommands(
    app_repo=app_repo, prompt_version_repo=prompt_version_repo
)

db_adpater = DBAdapter()

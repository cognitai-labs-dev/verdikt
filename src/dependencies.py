from src.config import Settings, settings
from src.evaluation.commands import EvaluationCommands
from src.evaluation.queries import EvaluationQueries
from src.judgement.commands import JudgementCommands
from src.judgement.queries import JudgementQueries
from src.repositories.evaluation import EvaluationsRepository
from src.repositories.judgment import JudgmentRepository
from src.repositories.sample import SamplesRepository
from src.sample.queries import SampleQueries

# Repositories


def build_evaluation_repo() -> EvaluationsRepository:
    return EvaluationsRepository()


def build_judgment_repo() -> JudgmentRepository:
    return JudgmentRepository()


def build_sample_repo() -> SamplesRepository:
    return SamplesRepository()


# Queries


def build_judgement_queries() -> JudgementQueries:
    return JudgementQueries()


def build_sample_queries() -> SampleQueries:
    return SampleQueries(
        judgment_repo=build_judgment_repo(),
        sample_repo=build_sample_repo(),
        evaluation_repo=build_evaluation_repo(),
        judgement_queries=build_judgement_queries(),
    )


def build_evaluation_queries() -> EvaluationQueries:
    return EvaluationQueries(
        sample_queries=build_sample_queries(),
    )


# Commands


def build_judgement_commands() -> JudgementCommands:
    return JudgementCommands(
        judgment_repo=build_judgment_repo(),
    )


def build_evaluation_commands(
    app_settings: Settings = settings,
) -> EvaluationCommands:
    return EvaluationCommands(
        settings=app_settings,
        evaluation_repo=build_evaluation_repo(),
        sample_repo=build_sample_repo(),
        judgment_repo=build_judgment_repo(),
    )

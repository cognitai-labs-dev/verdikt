from sqlalchemy.schema import MetaData

from .evaluations import evaluations_table as evaluations
from .evaluation_runs import evaluation_runs_table as evaluations_runs
from .judge_results import judge_results_table as judge_results

sa_metadata = MetaData()

__all__ = [
    "sa_metadata",
    "evaluations",
    "evaluations_runs",
    "judge_results",
]

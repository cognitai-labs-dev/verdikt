from sqlalchemy.schema import MetaData

from .evaluations import evaluations_table as evaluations
from .evaluation_runs import evaluation_runs_table as evaluations_runs
from .judges import judges_table as judges

sa_metadata = MetaData()

__all__ = [
    "sa_metadata",
    "evaluations",
    "evaluations_runs",
    "judges",
]

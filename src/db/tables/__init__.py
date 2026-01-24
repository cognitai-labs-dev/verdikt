from sqlalchemy.schema import MetaData

from .evaluations import evaluations_table as evaluations
from .samples import samples_table as samples
from .judgments import judgments_table as judgments

sa_metadata = MetaData()

__all__ = [
    "sa_metadata",
    "evaluations",
    "samples",
    "judgments",
]

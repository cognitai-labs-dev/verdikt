from src.crud.base import BaseCRUD
from src.db.tables.evaluation_runs import evaluation_runs_table
from src.schemas.base import UpdateSchema
from src.schemas.evaluation_run import EvaluationRunCreateSchema, EvaluationRunSchema


class EvaluationRunsCRUD(
    BaseCRUD[EvaluationRunCreateSchema, EvaluationRunSchema, UpdateSchema]
):
    """Data access layer for evaluation runs operations."""

    def __init__(self):
        super().__init__(evaluation_runs_table, EvaluationRunSchema)


evaluation_runs_crud = EvaluationRunsCRUD()

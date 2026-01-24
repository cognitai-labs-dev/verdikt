from src.crud.base import BaseCRUD
from src.db.tables.evaluations import evaluations_table
from src.schemas.base import UpdateSchema
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema


class EvaluationsCRUD(BaseCRUD[EvaluationCreateSchema, EvaluationSchema, UpdateSchema]):
    """Data access layer for evaluations operations."""

    def __init__(self):
        super().__init__(evaluations_table, EvaluationSchema)


evaluations_crud = EvaluationsCRUD()

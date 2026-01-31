from collections import defaultdict

from sqlalchemy import and_, select

from src.constants import JudgmentStatus, JudgmentType
from src.db.tables.judgments import judgments_table
from src.repositories.base import BaseRepository
from src.schemas.judgment import (
    JudgmentCreateSchema,
    JudgmentSchema,
    JudgmentUpdateSchema,
)


class JudgmentRepository(
    BaseRepository[
        JudgmentCreateSchema, JudgmentSchema, JudgmentUpdateSchema
    ]
):
    """Data access layer for judgment operations."""

    def __init__(self):
        super().__init__(judgments_table, JudgmentSchema)

    def get_many_pending(self, limit: int) -> list[JudgmentSchema]:
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.status == JudgmentStatus.PENDING,
                    self.table.c.judgment_type == JudgmentType.LLM,
                )
            )
            .order_by(self.table.c.created_at.desc())
            .limit(limit)
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [
            JudgmentSchema.model_validate(row._mapping)
            for row in rows
        ]

    def get_many_by_sample_ids(
        self, sample_ids: list[int], judgment_type: JudgmentType
    ) -> dict[int, list[JudgmentSchema]]:
        if not sample_ids:
            return {}

        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.sample_id.in_(sample_ids),
                    self.table.c.judgment_type == judgment_type,
                )
            )
            .order_by(
                self.table.c.sample_id, self.table.c.created_at.desc()
            )
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        grouped: dict[int, list[JudgmentSchema]] = defaultdict(list)
        for row in rows:
            judgment = JudgmentSchema.model_validate(row._mapping)
            grouped[judgment.sample_id].append(judgment)

        return dict(grouped)

    def get_human_judgments_by_sample_ids(
        self, sample_ids: list[int]
    ) -> dict[int, JudgmentSchema | None]:
        grouped = self.get_many_by_sample_ids(
            sample_ids, JudgmentType.HUMAN
        )
        return {
            sample_id: self._extract_human_judgment(
                grouped.get(sample_id, [])
            )
            for sample_id in sample_ids
        }

    def get_llm_judgmenets_by_sample_id(
        self, sample_id: int
    ) -> list[JudgmentSchema]:
        return self.get_many_by_sample_ids(
            [sample_id], JudgmentType.LLM
        ).get(sample_id, [])

    def get_human_judgement_by_sample_id(
        self, sample_id: int
    ) -> JudgmentSchema | None:
        return self.get_human_judgments_by_sample_ids(
            [sample_id]
        ).get(sample_id)

    @staticmethod
    def _extract_human_judgment(
        judgments: list[JudgmentSchema],
    ) -> JudgmentSchema | None:
        if len(judgments) == 0:
            return None
        if len(judgments) == 1:
            return judgments[0]
        raise RuntimeError("More than 1 human judgment for a sample")


judgment_repository = JudgmentRepository()

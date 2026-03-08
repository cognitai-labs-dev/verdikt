import hashlib

from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.app_dataset import AppDatasetRepository
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
    AppDatasetUpdateSchema,
)


class AppDatasetQueries:
    def __init__(
        self, app_dataset_repo: AppDatasetRepository
    ) -> None:
        self.repo = app_dataset_repo

    def _sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    async def sync_datasets(
        self,
        conn: AsyncConnection,
        app_id: int,
        items: list[
            tuple[str, str]
        ],  # [(question, human_answer), ...]
    ) -> tuple[list[AppDatasetSchema], bool]:
        """Sync incoming question/answer pairs against existing datasets.

        Hashes all questions and answers up front, then:
        - existing question, same answer   → no-op
        - existing question, answer differs → update human_answer
        - new question                      → insert

        Returns the full resulting list and a bool that is True if any
        new rows were inserted (so the route can return 201 vs 200).
        """
        existing = await self.repo.get_many_by_app_id(conn, app_id)

        # Hash everything up front — O(1) comparisons from here on
        incoming_hashed: dict[str, tuple[str, str]] = {
            self._sha256(q.strip()): (q.strip(), a.strip())
            for q, a in items
        }
        existing_hashed: dict[str, AppDatasetSchema] = {
            self._sha256(dataset.question.strip()): dataset
            for dataset in existing
        }

        to_insert: list[AppDatasetCreateSchema] = []
        to_update: list[tuple[AppDatasetSchema, str]] = []
        unchanged: list[AppDatasetSchema] = []

        for q_hash, dataset in existing_hashed.items():
            if q_hash not in incoming_hashed:
                unchanged.append(dataset)
            else:
                _, incoming_answer = incoming_hashed.pop(q_hash)
                if self._sha256(incoming_answer) == self._sha256(
                    dataset.human_answer.strip()
                ):
                    unchanged.append(dataset)
                else:
                    to_update.append((dataset, incoming_answer))

        # anything remaining in incoming_hashed has no existing match → insert
        for question, human_answer in incoming_hashed.values():
            to_insert.append(
                AppDatasetCreateSchema(
                    question=question,
                    human_answer=human_answer,
                    app_id=app_id,
                )
            )

        results: list[AppDatasetSchema] = list(unchanged)

        inserted = await self.repo.create_many(conn, to_insert)
        results.extend(inserted)

        for dataset, new_answer in to_update:
            updated = await self.repo.update(
                conn,
                AppDatasetUpdateSchema(
                    id=dataset.id,
                    human_answer=new_answer,
                ),
            )
            if updated is not None:
                results.append(updated)

        any_inserted = len(to_insert) > 0
        return results, any_inserted

from sqlalchemy.ext.asyncio import AsyncConnection

from src.judgement.prompts import JUDGE_SYSTEM_PROMPT
from src.repositories.apps import AppsRepository
from src.repositories.prompt_version import PromptVersionRepository
from src.schemas.app import (
    AppCreateSchema,
    AppUpdateSchema,
)
from src.schemas.prompt_version import PromptVersionCreateSchema


class AppCommands:
    def __init__(
        self,
        app_repo: AppsRepository,
        prompt_version_repo: PromptVersionRepository,
    ) -> None:
        self.app_repo = app_repo
        self.prompt_repo = prompt_version_repo

    async def create(
        self, conn: AsyncConnection, name: str, slug: str
    ):
        app = await self.app_repo.create(
            conn,
            AppCreateSchema(name=name, slug=slug),
        )

        prompt = await self.prompt_repo.create(
            conn,
            PromptVersionCreateSchema(
                app_id=app.id,
                content=JUDGE_SYSTEM_PROMPT,
            ),
        )

        await self.app_repo.update(
            conn,
            AppUpdateSchema(
                id=app.id,
                current_prompt_version_id=prompt.id,
            ),
        )

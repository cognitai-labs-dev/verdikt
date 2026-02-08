from sqlalchemy.ext.asyncio import AsyncConnection

from src.app.schemas import AppWithPrompts
from src.repositories.apps import AppsRepository
from src.repositories.prompt_version import PromptVersionRepository


class AppQueries:
    def __init__(
        self,
        app_repo: AppsRepository,
        prompt_version_repo: PromptVersionRepository,
    ) -> None:
        self.app_repo = app_repo
        self.prompt_repo = prompt_version_repo

    async def get_app_with_prompt(
        self, conn: AsyncConnection, app_id: int
    ) -> AppWithPrompts | None:
        app = await self.app_repo.get(conn, app_id)
        if app is None:
            return None
        prompt = await self.prompt_repo.get(
            conn, app.current_prompt_version_id
        )
        if prompt is None:
            return None

        return AppWithPrompts(
            **app.model_dump(),
            judge_prompt=prompt.content,
            judge_prompt_hash=prompt.hash,
        )

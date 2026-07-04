import logging

import yaml
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.apps import AppsRepository

logger = logging.getLogger(__name__)


class AccessConfig(BaseModel):
    admins: list[str] = Field(default_factory=list)
    apps: dict[str, list[str]] = Field(default_factory=dict)


class AdminRegistry:
    """Access-config gateway: holds the admin emails and reconciles bindings.

    A single shared instance lives in ``src.dependencies``; ``authenticate``
    queries it (``email in admin_registry``) and the app lifespan calls
    ``load`` + ``reconcile`` on startup.
    """

    def __init__(
        self,
        app_repo: AppsRepository,
        app_principal_repo: AppPrincipalRepository,
    ) -> None:
        self.app_repo = app_repo
        self.app_principal_repo = app_principal_repo
        self._emails: set[str] = set()

    def __contains__(self, email: str) -> bool:
        return email in self._emails

    def replace(self, emails: list[str]) -> None:
        self._emails = {
            email.strip() for email in emails if email.strip()
        }

    @staticmethod
    def load(path: str) -> AccessConfig:
        """Parse the access config YAML file at `path`."""
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
        return AccessConfig.model_validate(raw)

    async def reconcile(
        self, conn: AsyncConnection, cfg: AccessConfig
    ) -> None:
        """Make EMAIL bindings match the config and refresh the admin set.

        For each app slug listed: add emails that are missing and remove
        emails that are present but no longer listed. Apps that do not exist
        are logged and skipped (a nonexistent app cannot be bound).
        """
        logger.info(
            "access config: reconciling %d admin(s) and %d app(s)",
            len(cfg.admins),
            len(cfg.apps),
        )
        self.replace(cfg.admins)
        logger.info("access config: admins = %s", sorted(cfg.admins))

        total_added = 0
        total_removed = 0
        for slug, emails in cfg.apps.items():
            app = await self.app_repo.get_by_slug(conn, slug)
            if app is None:
                logger.warning(
                    "access config: app '%s' not found — skipping its %d "
                    "email binding(s)",
                    slug,
                    len(emails),
                )
                continue

            desired = {
                email.strip() for email in emails if email.strip()
            }
            current = set(
                await self.app_principal_repo.subjects_for(
                    conn, app.id, SubjectType.EMAIL
                )
            )

            to_add = desired - current
            to_remove = current - desired
            for email in to_add:
                await self.app_principal_repo.add(
                    conn, app.id, SubjectType.EMAIL, email
                )
            for email in to_remove:
                await self.app_principal_repo.remove(
                    conn, app.id, SubjectType.EMAIL, email
                )

            total_added += len(to_add)
            total_removed += len(to_remove)
            if to_add or to_remove:
                logger.info(
                    "access config: app '%s' — added %s, removed %s",
                    slug,
                    sorted(to_add) or "none",
                    sorted(to_remove) or "none",
                )
            else:
                logger.info(
                    "access config: app '%s' — already in sync (%d email(s))",
                    slug,
                    len(desired),
                )

        logger.info(
            "access config: reconciliation done — %d email binding(s) added, "
            "%d removed across %d app(s)",
            total_added,
            total_removed,
            len(cfg.apps),
        )

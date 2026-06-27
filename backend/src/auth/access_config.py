"""Declarative email-principals config (GitOps).

A YAML file is the source of truth for which human emails may access the apps
it lists, plus which emails are admins. It is loaded and reconciled on startup:
for every app slug present in the file, the app's EMAIL bindings are made to
match the listed emails exactly. CLIENT bindings, and apps not mentioned in the
file, are left untouched.

Example::

    admins:
      - alice@example.com
    apps:
      my-app:
        - bob@example.com
        - carol@example.com
"""

import logging

import yaml
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from src.repositories.apps import AppsRepository

logger = logging.getLogger(__name__)

# Emails granted admin via the config file. Unioned with APISettings.admin_emails
# by `authenticate`. Repopulated wholesale on every reconcile.
admin_registry: set[str] = set()


class AccessConfig(BaseModel):
    admins: list[str] = Field(default_factory=list)
    apps: dict[str, list[str]] = Field(default_factory=dict)


def load(path: str) -> AccessConfig:
    """Parse the access config YAML file at `path`."""
    with open(path) as fh:
        raw = yaml.safe_load(fh) or {}
    return AccessConfig.model_validate(raw)


async def reconcile(
    conn: AsyncConnection,
    app_repo: AppsRepository,
    app_principal_repo: AppPrincipalRepository,
    cfg: AccessConfig,
) -> None:
    """Make EMAIL bindings match the config and refresh the admin registry.

    For each app slug listed: add emails that are missing and remove emails
    that are present but no longer listed. Apps that do not exist are logged
    and skipped (a nonexistent app cannot be bound).
    """
    global admin_registry
    admin_registry = {
        email.strip() for email in cfg.admins if email.strip()
    }

    for slug, emails in cfg.apps.items():
        app = await app_repo.get_by_slug(conn, slug)
        if app is None:
            logger.warning(
                "access config references unknown app '%s' — skipping",
                slug,
            )
            continue

        desired = {email.strip() for email in emails if email.strip()}
        current = set(
            await app_principal_repo.subjects_for(
                conn, app.id, SubjectType.EMAIL
            )
        )

        for email in desired - current:
            await app_principal_repo.add(
                conn, app.id, SubjectType.EMAIL, email
            )
        for email in current - desired:
            await app_principal_repo.remove(
                conn, app.id, SubjectType.EMAIL, email
            )

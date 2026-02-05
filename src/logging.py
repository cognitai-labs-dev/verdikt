import logging

from src.config import AppSettings

logger = logging.getLogger(__name__)


def setup_logging():
    settings = AppSettings()
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

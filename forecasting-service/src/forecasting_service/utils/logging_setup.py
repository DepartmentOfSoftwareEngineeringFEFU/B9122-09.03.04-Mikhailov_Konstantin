import sys
from loguru import logger

from forecasting_service.config import LOGS_DIR


def setup_logging(
    log_prefix: str = "app",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | {message}"
        ),
        level=console_level,
    )

    logger.add(
        str(LOGS_DIR / f"{log_prefix}_{{time:YYYY-MM-DD}}.log"),
        level=file_level,
        rotation="10 MB",
    )
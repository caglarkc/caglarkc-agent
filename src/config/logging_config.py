from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler

from src.config.settings import get_settings


DAEMON_LOG_MAX_BYTES = 10 * 1024 * 1024
DAEMON_LOG_BACKUP_COUNT = 5


def configure_logging(*, daemon_mode: bool = False) -> None:
    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = RichHandler(
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    console_handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))

    file_handler = RotatingFileHandler(
        filename=settings.log_file_path,
        maxBytes=max(settings.log_max_bytes, DAEMON_LOG_MAX_BYTES) if daemon_mode else settings.log_max_bytes,
        backupCount=max(settings.log_backup_count, DAEMON_LOG_BACKUP_COUNT)
        if daemon_mode
        else settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

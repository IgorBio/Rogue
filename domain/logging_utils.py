"""Logging helpers for swallowed exceptions and app setup."""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_DEFAULT_LOG_DIR = Path("logs")
_DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "rogue.log"


def setup_logging(
    level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file: Path = _DEFAULT_LOG_FILE,
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
) -> None:
    """Configure root logging with console + rotating file handlers."""
    root = logging.getLogger()
    if root.handlers:
        return

    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    root.setLevel(min(level, file_level))
    root.addHandler(console)
    root.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger for a module."""
    return logging.getLogger(name if name else __name__)


def log_exception(exc: Exception, context: str = "") -> None:
    """Log an exception without raising."""
    logger = get_logger(context if context else __name__)
    logger.exception("Unhandled exception: %s", exc)

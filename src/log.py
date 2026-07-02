# log.py
import logging


# Log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


class _ShortLevelFormatter(logging.Formatter):
    """Formatter with short level names."""

    def format(self, record: logging.LogRecord) -> str:
        record.levelname_short = {
            "DEBUG": "D",
            "INFO": "I",
            "WARNING": "W",
            "ERROR": "E",
            "CRITICAL": "C",
        }.get(record.levelname, record.levelname)
        try:
            return super().format(record)
        finally:
            if hasattr(record, "levelname_short"):
                delattr(record, "levelname_short")


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure the logger.

    Args:
        level: Log level, defaults to INFO.
    """
    logger = logging.getLogger("RA")
    if not logger.hasHandlers():
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(_ShortLevelFormatter("%(name)s.%(levelname_short)s: %(message)s"))
        logger.addHandler(handler)
    else:
        logger.setLevel(level)
    return logger


def set_log_level(level_name: str) -> None:
    """Set the log level.

    Args:
        level_name: Log level name (DEBUG/INFO/WARNING/ERROR).
    """
    level = LOG_LEVELS.get(level_name, logging.INFO)
    log.setLevel(level)


log: logging.Logger = setup_logger(logging.DEBUG)
"""RA logger instance."""

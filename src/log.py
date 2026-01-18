# log.py
import logging


class _ShortLevelFormatter(logging.Formatter):
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


def setup_logger() -> logging.Logger:
    """配置日志"""
    logger = logging.getLogger("RA")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        # logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(_ShortLevelFormatter("%(name)s.%(levelname_short)s: %(message)s"))

        logger.addHandler(handler)
    return logger


log: logging.Logger = setup_logger()
""" RA 日志实例 """

# log.py
import logging


def setup_logger() -> logging.Logger:
    """配置日志"""
    logger = logging.getLogger("RA")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        # logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()

        # 自定义日志级别简写
        def levelname_short(levelname):
            return {
                "DEBUG": "D",
                "INFO": "I",
                "WARNING": "W",
                "ERROR": "E",
                "CRITICAL": "C",
            }.get(levelname, levelname)

        # 修改格式化器，使用简写级别
        handler.setFormatter(
            logging.Formatter("%(name)s.%(levelname_short)s: %(message)s")
        )

        # 添加自定义过滤器来支持简写级别
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.levelname_short = levelname_short(record.levelname)
            return record

        logging.setLogRecordFactory(record_factory)

        logger.addHandler(handler)
    return logger


log: logging.Logger = setup_logger()
""" RA 日志实例 """

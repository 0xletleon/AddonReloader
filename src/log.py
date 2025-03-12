# log.py
import logging

def setup_logger():
    """配置日志"""
    logger = logging.getLogger("Addon Reloader")
    
    # 清除所有现有的处理器
    while logger.handlers:
        logger.handlers.pop()
    
    # 禁止日志传播到父记录器
    logger.propagate = False
    
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("Addon Reloader: %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger


log = setup_logger()
""" Addon Reloader 日志实例 """

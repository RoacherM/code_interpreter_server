"""
Author: ByronVon
Date: 2024-07-03 16:47:03
FilePath: /code_interpreter/log.py
Description: 
"""

from code_interpreter.config import LOG_PATH


def log_config(log_path):
    import logging
    from logging.handlers import RotatingFileHandler

    realtime_format = (
        "%(levelname)s %(asctime)s [%(filename)s:%(lineno)s]: \t %(message)s"
    )
    formatter = logging.Formatter(
        "%(levelname)s %(asctime)s [%(funcName)s] =====> [%(message)s]"
    )
    logging.basicConfig(level=logging.INFO, format=realtime_format)
    file_log_handler = RotatingFileHandler(
        log_path, encoding="UTF-8", maxBytes=1024 * 1024 * 100, backupCount=100
    )
    file_log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_log_handler)
    return logging


logging = log_config(LOG_PATH)

import logging.handlers
import pathlib
import sys
from typing import Optional


inited: bool = False


def init_logger(path: Optional[pathlib.Path]) -> None:
    logger: logging.Logger = logging.getLogger()
    formatter: logging.Formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

    if path:
        handler: logging.Handler = logging.handlers.RotatingFileHandler(path, maxBytes=10 ** 5, backupCount=1)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    global inited
    inited = True


def get_logger(name) -> logging.Logger:
    if not inited:
        print('Logger is not initialized yet', file=sys.stderr)
    return logging.getLogger(name)

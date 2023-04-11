import logging.handlers
import pathlib
import sys
from typing import Optional

inited: bool = False


def init_logger(path: Optional[pathlib.Path]) -> None:
    global inited
    if inited:
        return

    logger: logging.Logger = logging.getLogger()
    formatter: logging.Formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

    if path:
        handler: logging.Handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=10 ** 5, backupCount=1, encoding='utf-8')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    inited = True


def get_logger(name: str = str(__package__).removesuffix('_sdk')) -> logging.Logger:
    if not inited:
        print('Logger is not initialized yet', file=sys.stderr)
    return logging.getLogger(name)

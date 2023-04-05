import logging.handlers

from .constant import PROG_NAME

logger: logging.Logger = logging.getLogger()
formatter: logging.Formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

handler: logging.Handler = logging.handlers.RotatingFileHandler(f'{PROG_NAME}.log', maxBytes=10 ** 5, backupCount=1)
handler.setFormatter(formatter)
logger.addHandler(handler)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)


def get_logger(name) -> logging.Logger:
    return logging.getLogger(name)

import logging

from .types_ import LOG_LEVEL_TYPE


def configure_logging(level: LOG_LEVEL_TYPE, fmt: str, datefmt: str) -> None:
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
    )

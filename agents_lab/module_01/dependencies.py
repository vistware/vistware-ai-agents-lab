from agents_lab.module_01.settings import module_settings
from agents_lab.utils.logging_ import configure_logging


def project_init() -> None:
    configure_logging(
        level=module_settings.LOG_LEVEL,
        fmt=module_settings.LOG_FORMAT,
        datefmt=module_settings.LOG_DATE_FORMAT,
    )

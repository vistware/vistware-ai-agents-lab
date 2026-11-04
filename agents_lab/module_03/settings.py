from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from agents_lab.utils.types_ import LOG_LEVEL_TYPE


class Module03Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    AI_MODEL: str
    AI_MODEL_REASONING_EFFORT: Literal[
        "none", "minimal", "low", "medium", "high", "xhigh", "max"
    ]
    LOG_LEVEL: LOG_LEVEL_TYPE = "DEBUG"
    LOG_FORMAT: str = "[%(asctime)s][%(levelname)s] - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


module_settings = Module03Settings()

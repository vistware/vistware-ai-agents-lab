from pydantic import SecretStr
from pydantic_settings import BaseSettings

from agents_lab.utils.types_ import LOG_LEVEL_TYPE


class Module01Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    AI_MODEL: str
    LOG_LEVEL: LOG_LEVEL_TYPE = "DEBUG"
    LOG_FORMAT: str = "[%(asctime)s][%(levelname)s] - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


module_settings = Module01Settings()

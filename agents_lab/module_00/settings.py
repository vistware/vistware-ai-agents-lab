from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Module00Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    AI_MODEL: str

module_settings = Module00Settings()

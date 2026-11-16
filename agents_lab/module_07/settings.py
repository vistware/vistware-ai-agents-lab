from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath, SecretStr
from pydantic_settings import BaseSettings

from agents_lab.utils.types_ import LOG_LEVEL_TYPE


class Module07Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    AI_MODEL: str
    AI_MODEL_REASONING_EFFORT: Literal[
        "none", "minimal", "low", "medium", "high", "xhigh", "max"
    ]
    LOG_LEVEL: LOG_LEVEL_TYPE = "DEBUG"
    LOG_FORMAT: str = "[%(asctime)s][%(levelname)s] - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    INC_KNOWLEDGE_DIR: DirectoryPath = Path("data/module_07/knowledge")
    INC_PARSED_KNOWLEDGE_FILE: Path = Path(
        "data/module_07/knowledge_chunks/parsed_knowledge.json"
    )
    EMBEDDER_MODEL: str = "openai:text-embedding-3-small"
    EMBEDDED_KNOWLEDGE_FILE: Path = Path(
        "data/module_07/knowledge_embedded/embedded_knowledge.json"
    )


module_settings = Module07Settings()

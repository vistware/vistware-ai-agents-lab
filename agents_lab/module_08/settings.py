from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from agents_lab.utils.types_ import LOG_LEVEL_TYPE

type ReasoningEffort = Literal[
    "none", "minimal", "low", "medium", "high", "xhigh", "max"
]


class Module08Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    ROOT_CAUSE_ANALYST_MODEL: str
    ROOT_CAUSE_ANALYST_REASONING_EFFORT: ReasoningEffort
    RECOVERY_PLANNER_MODEL: str
    RECOVERY_PLANNER_REASONING_EFFORT: ReasoningEffort
    INCIDENT_ORCHESTRATOR_MODEL: str
    INCIDENT_ORCHESTRATOR_REASONING_EFFORT: ReasoningEffort
    LOG_LEVEL: LOG_LEVEL_TYPE = "DEBUG"
    LOG_FORMAT: str = "[%(asctime)s][%(levelname)s] - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    INC_PARSED_KNOWLEDGE_FILE: Path = Path(
        "data/module_07/knowledge_chunks/parsed_knowledge.json"
    )
    EMBEDDER_MODEL: str = "openai:text-embedding-3-small"
    EMBEDDED_KNOWLEDGE_FILE: Path = Path(
        "data/module_07/knowledge_embedded/embedded_knowledge.json"
    )


module_settings = Module08Settings()

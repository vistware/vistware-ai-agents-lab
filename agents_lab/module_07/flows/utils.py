import json
from pathlib import Path

from ..settings import module_settings
from .schemas import (
    EmbeddedKnowledgeChunk,
    ParsedKnowledgeFile,
)


def _load_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        return {}
    with path.open("r") as file:
        return json.load(file)


def load_parsed_knowledge_files() -> dict[str, ParsedKnowledgeFile]:
    stored_data = _load_json(module_settings.INC_PARSED_KNOWLEDGE_FILE)
    return {
        name: ParsedKnowledgeFile.model_validate(data)
        for name, data in stored_data.items()
    }


def load_embedded_knowledge_chunks() -> dict[str, EmbeddedKnowledgeChunk]:
    stored_data = _load_json(module_settings.EMBEDDED_KNOWLEDGE_FILE)
    return {
        name: EmbeddedKnowledgeChunk.model_validate(data)
        for name, data in stored_data.items()
    }

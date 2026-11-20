import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from pydantic import ValidationError

from ..exceptions import KnowledgeIndexError
from ..settings import module_settings
from .schemas import (
    EmbeddedKnowledgeIndex,
    KnowledgeChunkWithSource,
    ParsedKnowledgeFile,
)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    )
    temporary_path = Path(temporary_file.name)
    try:
        with temporary_file:
            json.dump(data, temporary_file, indent=4)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_parsed_knowledge_files(
    *, required: bool = False
) -> dict[str, ParsedKnowledgeFile]:
    try:
        contents = module_settings.INC_PARSED_KNOWLEDGE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        if required:
            raise KnowledgeIndexError(
                "Parsed knowledge is missing. Run parse-knowledge first."
            ) from exc
        return {}
    stored_data = json.loads(contents) if contents else {}
    return {
        file_name: ParsedKnowledgeFile.model_validate(data)
        for file_name, data in stored_data.items()
    }


def load_parsed_knowledge_chunks() -> dict[str, KnowledgeChunkWithSource]:
    return {
        chunk.chunk_id: KnowledgeChunkWithSource(
            **chunk.model_dump(), file_name=file.name, file_path=file.path
        )
        for file in load_parsed_knowledge_files(required=True).values()
        for chunk in file.chunks
    }


def load_embedded_knowledge_index() -> EmbeddedKnowledgeIndex | None:
    try:
        contents = module_settings.EMBEDDED_KNOWLEDGE_FILE.read_bytes()
    except FileNotFoundError:
        return None
    try:
        return EmbeddedKnowledgeIndex.model_validate_json(contents)
    except ValidationError as exc:
        raise KnowledgeIndexError(
            "The embedding index is invalid or predates model metadata. Run embed-knowledge."
        ) from exc

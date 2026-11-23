from pydantic import TypeAdapter, ValidationError

from ..exceptions import KnowledgeIndexError
from ..settings import module_settings
from .schemas import (
    EmbeddedKnowledgeIndex,
    KnowledgeChunkWithSource,
    ParsedKnowledgeFile,
)

PARSE_KNOWLEDGE_COMMAND = "task run:module_07:parse-knowledge"
EMBED_KNOWLEDGE_COMMAND = "task run:module_07:embed-knowledge"

_parsed_files = TypeAdapter(dict[str, ParsedKnowledgeFile])


def load_parsed_knowledge_files(
    *, required: bool = False
) -> dict[str, ParsedKnowledgeFile]:
    path = module_settings.INC_PARSED_KNOWLEDGE_FILE
    try:
        contents = path.read_bytes()
    except FileNotFoundError as exc:
        if required:
            raise KnowledgeIndexError(
                f"Parsed knowledge is missing. Run `{PARSE_KNOWLEDGE_COMMAND}` first."
            ) from exc
        return {}
    except OSError as exc:
        raise KnowledgeIndexError(f"Cannot read parsed knowledge at {path}.") from exc
    try:
        return _parsed_files.validate_json(contents) if contents else {}
    except ValidationError as exc:
        raise KnowledgeIndexError(
            f"Parsed knowledge is invalid. Run `{PARSE_KNOWLEDGE_COMMAND}`."
        ) from exc


def load_parsed_knowledge_chunks() -> dict[str, KnowledgeChunkWithSource]:
    return {
        chunk.chunk_id: KnowledgeChunkWithSource(
            **chunk.model_dump(), file_name=file.name, file_path=file.path
        )
        for file in load_parsed_knowledge_files(required=True).values()
        for chunk in file.chunks
    }


def load_embedded_knowledge_index() -> EmbeddedKnowledgeIndex | None:
    path = module_settings.EMBEDDED_KNOWLEDGE_FILE
    try:
        contents = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise KnowledgeIndexError(
            f"Cannot read the embedding index at {path}."
        ) from exc
    try:
        return EmbeddedKnowledgeIndex.model_validate_json(contents)
    except ValidationError as exc:
        raise KnowledgeIndexError(
            "The embedding index is invalid or predates model metadata. "
            f"Run `{EMBED_KNOWLEDGE_COMMAND}`."
        ) from exc


def load_searchable_knowledge_index() -> EmbeddedKnowledgeIndex:
    index = load_embedded_knowledge_index()
    if index is None:
        raise KnowledgeIndexError(
            f"The embedding index is missing. Run `{EMBED_KNOWLEDGE_COMMAND}`."
        )
    if index.model != module_settings.EMBEDDER_MODEL:
        raise KnowledgeIndexError(
            "The embedding index uses a different model. "
            f"Run `{EMBED_KNOWLEDGE_COMMAND}`."
        )

    sources = load_parsed_knowledge_chunks()
    if index.chunks.keys() != sources.keys() or any(
        chunk.model_dump(exclude={"embedding"}) != sources[chunk_id].model_dump()
        for chunk_id, chunk in index.chunks.items()
    ):
        raise KnowledgeIndexError(
            "The index is out of sync with parsed knowledge. "
            f"Run `{EMBED_KNOWLEDGE_COMMAND}`."
        )
    return index

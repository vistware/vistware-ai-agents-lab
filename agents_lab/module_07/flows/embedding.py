import json
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Embedder

from agents_lab.module_07.settings import module_settings

from .schemas import EmbeddedKnowledgeChunk, ParsedKnowledgeFile
from .utils import load_embedded_knowledge_chunks, load_parsed_knowledge_files


@dataclass
class KnowledgeEmbedder:
    def __post_init__(self) -> None:
        self._embedder = Embedder(model=module_settings.EMBEDDER_MODEL)
        self._parsed_files: dict[str, ParsedKnowledgeFile] = {}
        self._embedded_chunks: dict[str, EmbeddedKnowledgeChunk] = {}

    def _load_existing_files(self) -> None:
        self._embedded_chunks = load_embedded_knowledge_chunks()
        self._parsed_files = load_parsed_knowledge_files()

    def _save_file[T: EmbeddedKnowledgeChunk | ParsedKnowledgeFile](
        self, path: Path, data: dict[str, T]
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized_files = {
            key: value.model_dump(mode="json") for key, value in data.items()
        }
        with path.open("w") as file:
            json.dump(serialized_files, file, indent=4)

    def _save_files(self) -> None:
        self._save_file(
            path=module_settings.EMBEDDED_KNOWLEDGE_FILE, data=self._embedded_chunks
        )
        self._save_file(
            path=module_settings.INC_PARSED_KNOWLEDGE_FILE,
            data=self._parsed_files,
        )

    async def embed(self) -> None:
        self._load_existing_files()
        for knowledge in self._parsed_files.values():
            if not knowledge.is_updated_or_new:
                continue
            self._embedded_chunks = {
                chunk_id: chunk
                for chunk_id, chunk in self._embedded_chunks.items()
                if chunk.file_name != knowledge.name
            }
            for chunk in knowledge.content:
                embedding_result = await self._embedder.embed_documents(
                    documents=[chunk.content]
                )
                embedded_chunk = EmbeddedKnowledgeChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    embedding=embedding_result.embeddings[0],
                    file_name=knowledge.name,
                    file_path=knowledge.path,
                )
                self._embedded_chunks[chunk.chunk_id] = embedded_chunk
            knowledge.is_updated_or_new = False
        self._save_files()


async def embed_knowledge_flow() -> None:
    knowledge_embedder = KnowledgeEmbedder()
    await knowledge_embedder.embed()

from ..exceptions import KnowledgeIndexError
from ..settings import module_settings
from .embedder import embedding_client
from .knowledge_storage import (
    load_embedded_knowledge_index,
    load_parsed_knowledge_chunks,
    write_json,
)
from .schemas import (
    EmbeddedKnowledgeChunk,
    EmbeddedKnowledgeIndex,
    KnowledgeChunkWithSource,
)


class KnowledgeEmbedder:
    async def embed(self, *, rebuild: bool = False) -> None:
        model = module_settings.EMBEDDER_MODEL
        sources = load_parsed_knowledge_chunks()
        previous_index = None if rebuild else self._load_reusable_index(model)
        index = await self._build_index(model, sources, previous_index)

        if sources != load_parsed_knowledge_chunks():
            raise KnowledgeIndexError(
                "Parsed knowledge changed during embedding. Run embed-knowledge again."
            )
        write_json(
            module_settings.EMBEDDED_KNOWLEDGE_FILE, index.model_dump(mode="json")
        )

    @staticmethod
    def _load_reusable_index(model: str) -> EmbeddedKnowledgeIndex | None:
        try:
            index = load_embedded_knowledge_index()
        except KnowledgeIndexError:
            return None
        if index is None or index.model != model:
            return None
        return index

    async def _build_index(
        self,
        model: str,
        sources: dict[str, KnowledgeChunkWithSource],
        previous_index: EmbeddedKnowledgeIndex | None,
    ) -> EmbeddedKnowledgeIndex:
        previous_chunks = previous_index.chunks if previous_index is not None else {}
        dimensions = previous_index.dimensions if previous_index is not None else None
        embedded_chunks: dict[str, EmbeddedKnowledgeChunk] = {}
        for chunk_id, source in sources.items():
            chunk = await self._embed_chunk(
                source, previous_chunks.get(chunk_id), dimensions
            )
            embedded_chunks[chunk_id] = chunk
            dimensions = len(chunk.embedding)

        return EmbeddedKnowledgeIndex(
            model=model,
            dimensions=dimensions if embedded_chunks else None,
            chunks=embedded_chunks,
        )

    @staticmethod
    async def _embed_chunk(
        source: KnowledgeChunkWithSource,
        previous_chunk: EmbeddedKnowledgeChunk | None,
        dimensions: int | None,
    ) -> EmbeddedKnowledgeChunk:
        if previous_chunk is not None and previous_chunk.content == source.content:
            vector = previous_chunk.embedding
        else:
            result = await embedding_client.embed_documents(documents=[source.content])
            vector = result.embeddings[0]
        if not vector or (dimensions is not None and len(vector) != dimensions):
            raise KnowledgeIndexError(
                "The embedding model returned unexpected dimensions. "
                "Run embed-knowledge --rebuild to regenerate the index."
            )
        return EmbeddedKnowledgeChunk(**source.model_dump(), embedding=vector)


async def embed_knowledge_flow(*, rebuild: bool = False) -> None:
    await KnowledgeEmbedder().embed(rebuild=rebuild)

from collections.abc import Sequence

import numpy as np

from ..exceptions import KnowledgeIndexError
from ..flows.embedder import embedding_client
from ..flows.knowledge_storage import (
    load_embedded_knowledge_index,
    load_parsed_knowledge_chunks,
)
from ..flows.schemas import EmbeddedKnowledgeIndex
from ..settings import module_settings
from .schemas import KnowledgeSearchResult

DEFAULT_SEARCH_RESULTS = 3
MAX_SEARCH_RESULTS = 5


class SemanticRetriever:
    async def search(
        self, query: str, top_k: int = DEFAULT_SEARCH_RESULTS
    ) -> list[KnowledgeSearchResult]:
        query = self._validate_search_arguments(query, top_k)
        index = self._load_searchable_index()
        if not index.chunks:
            return []

        query_embedding = await self._embed_query(query, index.dimensions)
        return self._rank_chunks(index, query, query_embedding)[:top_k]

    @staticmethod
    def _validate_search_arguments(query: str, top_k: int) -> str:
        query = query.strip()
        if not query:
            raise ValueError("Search query must not be blank.")
        if type(top_k) is not int or not 1 <= top_k <= MAX_SEARCH_RESULTS:
            raise ValueError(
                f"Top-K must be an integer between 1 and {MAX_SEARCH_RESULTS}."
            )
        return query

    @staticmethod
    def _load_searchable_index() -> EmbeddedKnowledgeIndex:
        index = load_embedded_knowledge_index()
        if index is None:
            raise KnowledgeIndexError(
                "The embedding index is missing. Run embed-knowledge."
            )
        if index.model != module_settings.EMBEDDER_MODEL:
            raise KnowledgeIndexError(
                "The embedding index uses a different model. Run embed-knowledge."
            )

        sources = load_parsed_knowledge_chunks()
        if index.chunks.keys() != sources.keys() or any(
            chunk.model_dump(exclude={"embedding"}) != sources[chunk_id].model_dump()
            for chunk_id, chunk in index.chunks.items()
        ):
            raise KnowledgeIndexError(
                "The index is out of sync with parsed knowledge. Run embed-knowledge."
            )
        return index

    @staticmethod
    async def _embed_query(query: str, dimensions: int | None) -> Sequence[float]:
        query_result = await embedding_client.embed_query(query=query)
        query_embedding = query_result.embeddings[0]
        if len(query_embedding) != dimensions:
            raise KnowledgeIndexError(
                "The query embedding dimensions differ from the index. "
                "Run embed-knowledge --rebuild."
            )
        return query_embedding

    @staticmethod
    def _rank_chunks(
        index: EmbeddedKnowledgeIndex, query: str, query_embedding: Sequence[float]
    ) -> list[KnowledgeSearchResult]:
        results = [
            KnowledgeSearchResult(
                query=query,
                file_name=chunk.file_name,
                file_path=chunk.file_path,
                similarity=float(np.dot(chunk.embedding, query_embedding)),
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in index.chunks.values()
        ]
        results.sort(key=lambda result: result.similarity, reverse=True)
        return results

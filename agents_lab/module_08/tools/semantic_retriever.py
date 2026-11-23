from collections.abc import Sequence
from math import isfinite

import numpy as np
from pydantic_ai import Embedder

from ..exceptions import KnowledgeIndexError
from ..flows.knowledge_storage import (
    EMBED_KNOWLEDGE_COMMAND,
    load_searchable_knowledge_index,
)
from ..flows.schemas import EmbeddedKnowledgeIndex
from ..settings import module_settings
from .schemas import KnowledgeSearchResult

DEFAULT_SEARCH_RESULTS = 3
MAX_SEARCH_RESULTS = 5


class SemanticRetriever:
    def __init__(self, *, embedder: Embedder | None = None) -> None:
        self._embedder = (
            embedder
            if embedder is not None
            else Embedder(model=module_settings.EMBEDDER_MODEL)
        )

    async def search(
        self, query: str, top_k: int = DEFAULT_SEARCH_RESULTS
    ) -> list[KnowledgeSearchResult]:
        query = query.strip()
        if not query:
            raise ValueError("Search query must not be blank.")
        if type(top_k) is not int or not 1 <= top_k <= MAX_SEARCH_RESULTS:
            raise ValueError(
                f"Top-K must be an integer between 1 and {MAX_SEARCH_RESULTS}."
            )
        index = load_searchable_knowledge_index()
        if not index.chunks:
            return []

        query_embedding = await self._embed_query(query, index.dimensions)
        return self._rank_chunks(index, query, query_embedding)[:top_k]

    async def _embed_query(self, query: str, dimensions: int | None) -> Sequence[float]:
        result = await self._embedder.embed_query(query=query)
        if len(result.embeddings) != 1:
            raise KnowledgeIndexError("The model did not return one query embedding.")
        embedding = result.embeddings[0]
        if len(embedding) != dimensions:
            raise KnowledgeIndexError(
                "The query embedding dimensions differ from the index. "
                f"Run `{EMBED_KNOWLEDGE_COMMAND} -- --rebuild`."
            )
        if not all(map(isfinite, embedding)):
            raise KnowledgeIndexError("The query embedding contains non-finite values.")
        return embedding

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

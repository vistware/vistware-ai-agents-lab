from dataclasses import dataclass

import numpy as np

from ..flows.embedder import embedder
from ..flows.utils import load_embedded_knowledge_chunks
from .schemas import SemanticRetrieverResult


@dataclass
class SemanticRetriever:
    def __post_init__(self) -> None:
        self._embedder = embedder
        self._knowledge_chunks = load_embedded_knowledge_chunks()

    async def retrieve(self, query: str, top_k: int) -> list[SemanticRetrieverResult]:
        query_embedding = (await self._embedder.embed_query(query=query)).embeddings[0]
        results = []
        for chunk in self._knowledge_chunks.values():
            similarity = np.dot(chunk.embedding, query_embedding)
            results.append(
                SemanticRetrieverResult(
                    query=query,
                    file_name=chunk.file_name,
                    file_path=chunk.file_path,
                    similarity=similarity,
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                )
            )
        results.sort(key=lambda chunk: chunk.similarity, reverse=True)
        return results[:top_k]

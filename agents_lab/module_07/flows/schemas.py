from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    PositiveInt,
    model_validator,
)


class KnowledgeSourceFile(BaseModel):
    source_id: str
    path: Path
    content_hash: str
    markdown: str


class ParsedKnowledgeChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: dict[str, Any]


class ParsedKnowledgeFile(BaseModel):
    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)

    name: str
    path: str
    content_hash: str = Field(alias="hash")
    chunks: list[ParsedKnowledgeChunk] = Field(alias="content")
    created_at: datetime
    chunking_version: int = 0


class KnowledgeChunkWithSource(ParsedKnowledgeChunk):
    file_name: str
    file_path: str


class EmbeddedKnowledgeChunk(KnowledgeChunkWithSource):
    embedding: list[FiniteFloat]


class EmbeddedKnowledgeIndex(BaseModel):
    model: str = Field(min_length=1)
    dimensions: PositiveInt | None
    chunks: dict[str, EmbeddedKnowledgeChunk]

    @model_validator(mode="after")
    def validate_dimensions(self) -> EmbeddedKnowledgeIndex:
        if any(
            len(chunk.embedding) != self.dimensions for chunk in self.chunks.values()
        ):
            raise ValueError("All embedding vectors must match the index dimensions")
        return self

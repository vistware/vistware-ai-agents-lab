from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from pydantic import BaseModel


class KnowledgeSourceFile(BaseModel):
    path: Path
    hash: str


class ChunkedKnowledgeFile(BaseModel):
    chunks: list[Document]
    source_file: KnowledgeSourceFile


class ParsedKnowledgeChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: dict[str, Any]


class ParsedKnowledgeFile(BaseModel):
    name: str
    path: str
    hash: str
    content: list[ParsedKnowledgeChunk]
    is_updated_or_new: bool
    created_at: datetime


class EmbeddedKnowledgeChunk(ParsedKnowledgeChunk):
    embedding: list[float]
    file_name: str
    file_path: str

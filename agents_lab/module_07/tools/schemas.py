from typing import Any

from pydantic import BaseModel


class SemanticRetrieverResult(BaseModel):
    query: str
    file_name: str
    file_path: str
    similarity: float
    chunk_id: str
    content: str
    metadata: dict[str, Any]

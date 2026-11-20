from typing import Any

from pydantic import BaseModel, Field


class KnowledgeSearchResult(BaseModel):
    query: str = Field(description="The search query used to find the knowledge chunk")
    file_name: str = Field(
        description="The name of the file containing the knowledge chunk"
    )
    file_path: str = Field(
        description="The path to the file containing the knowledge chunk"
    )
    similarity: float = Field(
        description="The similarity score between the query and the knowledge chunk"
    )
    chunk_id: str = Field(description="The unique identifier of the knowledge chunk")
    content: str = Field(description="The content of the knowledge chunk")
    metadata: dict[str, Any] = Field(
        description="Additional metadata associated with the knowledge chunk"
    )

from typing import Literal

from pydantic import BaseModel, Field


class IncidentInvestigationAnswer(BaseModel):
    answer: str = Field(
        min_length=1,
        description="Answer explaining the documented findings and any uncertainty",
    )
    knowledge_status: Literal["supported", "insufficient"] = Field(
        description="Whether the retrieved documentation is sufficient to answer"
    )
    chunk_ids: list[str] = Field(
        description="Exact IDs of the retrieved chunks cited in the answer"
    )

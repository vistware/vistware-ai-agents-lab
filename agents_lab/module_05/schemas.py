from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StatusLevel(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentRecord(BaseModel):
    id: Annotated[str, StringConstraints(to_upper=True)] = Field(
        validation_alias="ID",
        description="Unique identifier for the incident",
    )

    service: Annotated[str, StringConstraints(to_lower=True)] = Field(
        validation_alias="Service",
        description="Service affected by the incident",
    )
    severity: SeverityLevel = Field(
        description="Severity level of the incident", validation_alias="Severity"
    )
    status: StatusLevel = Field(
        description="Current status of the incident", validation_alias="Status"
    )
    created_at: str = Field(
        description="Timestamp when the incident was created",
    )
    description: str = Field(
        description="Detailed description of the incident",
    )


class IncidentAnalysis(BaseModel):
    summary: str = Field(description="Summary of the incident analysis")
    incidents: list[IncidentRecord] = Field(description="List of incident records")

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DeploymentStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class LogLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class IncidentDiagnosis(BaseModel):
    """
    Schema representing the diagnosis of an incident.
    """

    summary: str = Field(description="A brief summary of the incident")
    probable_root_cause: str | None = Field(
        description="The most likely root cause of the incident, if known"
    )
    evidence: list[str] = Field(
        description="A list of evidence supporting the diagnosis"
    )
    recommendations: list[str] = Field(
        description="Recommended actions to address the incident"
    )


class RecentDeployment(BaseModel):
    id: str = Field(description="The unique identifier of the deployment")
    service: str = Field(description="The name of the service being deployed")
    timestamp: datetime = Field(description="The timestamp of the deployment")
    status: DeploymentStatus = Field(description="The status of the deployment")


class LogEntry(BaseModel):
    id: str = Field(description="The unique identifier of the log entry")
    service: str = Field(description="The name of the service generating the log")
    timestamp: datetime = Field(description="The timestamp of the log entry")
    level: LogLevel = Field(description="The log level")
    message: str = Field(description="The log message")


class ServiceMetric(BaseModel):
    service: str = Field(description="The name of the service")
    timestamp: datetime = Field(description="The timestamp of the metric")
    cpu_usage: float = Field(description="The CPU usage percentage")
    memory_usage: float = Field(description="The memory usage percentage")
    disk_usage: float = Field(description="The disk usage percentage")
    password_expires_in: int = Field(
        description="Seconds until the password expires. 0 means it has expired."
    )


class UserInput(BaseModel):
    service: str = Field(
        description="The name of the service for which input is provided"
    )

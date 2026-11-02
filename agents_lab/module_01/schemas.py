from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class DeploymentStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class LogLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ActionType(StrEnum):
    TOOL = "tool"
    ANSWER = "answer"
    USER_INPUT = "user_input"


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


class ModelResponseSchema(BaseModel):
    action: ActionType = Field(
        description="The action taken by the model, either 'tool', 'answer', or 'user_input'. "
        "Use 'user_input' when the model requires input from the user."
        "Use 'tool' when the model takes an action using a tool."
        "Use 'answer' when the model provides an answer."
    )
    tool_name: str | None = Field(
        default=None, description="The name of the tool if the action is 'tool'"
    )
    tool_args: dict[str, str] | None = Field(
        default=None, description="The arguments for the tool if the action is 'tool'"
    )
    output: str | None = Field(
        default=None,
        description="The answer provided by the model if the action is 'answer' or 'user_input'",
    )
    reason: str = Field(description="The reason for the model's action")

    @model_validator(mode="after")
    def validate_action(self) -> Self:
        match self.action:
            case ActionType.TOOL:
                if not self.tool_name or not self.tool_name.strip():
                    raise ValueError("tool_name is required for TOOL action")

                if self.tool_args is None:
                    raise ValueError("tool_args is required for TOOL action")

                if self.output is not None:
                    raise ValueError("output must be null for TOOL action")

            case ActionType.ANSWER | ActionType.USER_INPUT:
                if not self.output or not self.output.strip():
                    raise ValueError("output is required for ANSWER or USER_INPUT")

                if self.tool_name is not None:
                    raise ValueError("tool_name must be null")

                if self.tool_args is not None:
                    raise ValueError("tool_args must be null")

        return self

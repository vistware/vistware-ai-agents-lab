from datetime import datetime
from typing import Annotated

from pydantic import Field
from pydantic_ai import RunContext

from .agent_deps import IncidentInvistigatorDeps
from .exceptions import ServicePermissionDeniedError
from .schemas import (
    DeploymentStatus,
    LogEntry,
    LogLevel,
    RecentDeployment,
    ServiceMetric,
)

AVAILABLE_SERVICES_FOR_USERS = {"USER_01": ["my_service"], "USER_02": ["my_service02"]}


def get_service_by_name(auth_user: str, service: str) -> str:
    services_for_user = AVAILABLE_SERVICES_FOR_USERS.get(auth_user, [])
    if service not in services_for_user:
        raise ServicePermissionDeniedError(service=service)
    return service


def get_recent_deployments(
    ctx: RunContext[IncidentInvistigatorDeps],
) -> list[RecentDeployment]:
    """
    Retrieve recent deployments for the given service.

    Args:
        ctx (RunContext[IncidentInvistigatorDeps]): The run context containing dependencies.

    Returns:
        list[RecentDeployment]: A list of recent deployments for the service.
    """
    exist_service: str = get_service_by_name(
        auth_user=ctx.deps.auth_user, service=ctx.deps.service
    )

    return [
        RecentDeployment(
            id="1",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
            status=DeploymentStatus.SUCCESS,
        ),
        RecentDeployment(
            id="2",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:00", "%Y-%m-%d %H:%M:%S"),
            status=DeploymentStatus.FAILED,
        ),
    ]


def get_recent_logs(
    ctx: RunContext[IncidentInvistigatorDeps], limit: Annotated[int, Field(gt=0)]
) -> list[LogEntry]:
    """
    Retrieve recent logs for the given service.

    Args:
        ctx (RunContext[IncidentInvistigatorDeps]): The run context containing dependencies.
        limit (int): The maximum number of log entries to retrieve.

    Returns:
        list[LogEntry]: A list of recent log entries for the service.
    """
    exist_service: str = get_service_by_name(
        auth_user=ctx.deps.auth_user, service=ctx.deps.service
    )
    logs = [
        LogEntry(
            id="7",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:50", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.ERROR,
            message="Restored old deployment failed Reason(Invalid password to database)",
        ),
        LogEntry(
            id="6",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:45", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.WARNING,
            message="Restarting service.",
        ),
        LogEntry(
            id="5",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:40", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.ERROR,
            message="Invalid password to database.",
        ),
        LogEntry(
            id="4",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:20", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.WARNING,
            message="Disk space running low.",
        ),
        LogEntry(
            id="3",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:10", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.INFO,
            message="New deployment is in progress.",
        ),
        LogEntry(
            id="2",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:01", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.INFO,
            message="New deployment has been started.",
        ),
        LogEntry(
            id="1",
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:00", "%Y-%m-%d %H:%M:%S"),
            level=LogLevel.INFO,
            message="Old deployment has been stopped.",
        ),
    ]
    return logs[:limit]


def get_service_metrics(
    ctx: RunContext[IncidentInvistigatorDeps],
) -> list[ServiceMetric]:
    """
    Retrieve service metrics for the given service.

    Args:
        ctx (RunContext[IncidentInvistigatorDeps]): The run context containing dependencies.

    Returns:
        list[ServiceMetric]: A list of service metrics for the service.
    """
    exist_service: str = get_service_by_name(
        auth_user=ctx.deps.auth_user, service=ctx.deps.service
    )
    return [
        ServiceMetric(
            service=exist_service,
            timestamp=datetime.strptime("2026-11-02 14:00:00", "%Y-%m-%d %H:%M:%S"),
            cpu_usage=80,
            memory_usage=70,
            disk_usage=95,
            password_expires_in=0,
        )
    ]

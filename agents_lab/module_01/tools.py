from datetime import datetime

from agents_lab.module_01.schemas import (
    DeploymentStatus,
    LogEntry,
    LogLevel,
    RecentDeployment,
    ServiceMetric,
)

from .exceptions import ServiceNotFoundError

AVAILABLE_SERVICE = "my_service"


def get_service_by_name(service: str) -> str:
    if service != AVAILABLE_SERVICE:
        raise ServiceNotFoundError(service=service)
    return AVAILABLE_SERVICE


def get_recent_deployments(service: str) -> list[RecentDeployment]:
    """
    Retrieve recent deployments for the given service.

    Args:
        service (str): The name of the service.

    Returns:
        list[RecentDeployment]: A list of recent deployments for the service.
    """
    exist_service: str = get_service_by_name(service=service)

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


def get_recent_logs(service: str, limit: str) -> list[LogEntry]:
    """
    Retrieve recent logs for the given service.

    Args:
        service (str): The name of the service.
        limit (str): The maximum number of log entries to retrieve.

    Returns:
        list[LogEntry]: A list of recent log entries for the service.
    """
    exist_service: str = get_service_by_name(service=service)
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
    return logs[: int(limit)]


def get_service_metrics(service: str) -> list[ServiceMetric]:
    """
    Retrieve service metrics for the given service.

    Args:
        service (str): The name of the service.

    Returns:
        list[ServiceMetric]: A list of service metrics for the service.
    """
    exist_service: str = get_service_by_name(service=service)
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

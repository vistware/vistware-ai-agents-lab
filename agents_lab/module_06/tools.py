import csv

from pydantic import ValidationError
from pydantic_ai.exceptions import ToolFailed

from .exceptions import InvalidFileFormatError
from .schemas import IncidentRecord, SeverityLevel, StatusLevel
from .settings import module_settings


def _read_incidents() -> list[IncidentRecord]:
    with module_settings.INCIDENTS_FILE.open() as inc_file:
        inc_reader = csv.DictReader(inc_file)
        incidents = [IncidentRecord.model_validate(row) for row in inc_reader]
    return incidents


def search_incidents(
    inc_ids: set[str] | None = None,
    service: str | None = None,
    severity: SeverityLevel | None = None,
    status: StatusLevel | None = None,
) -> list[IncidentRecord]:
    """
    Search for incidents based on the given filters.

    Args:
        inc_ids (set[str] | None): Set of incident IDs to filter by.
        service (str | None): Service name to filter by.
        severity (SeverityLevel | None): Severity level to filter by.
        status (StatusLevel | None): Status level to filter by.

    Returns:
        list[IncidentRecord]: List of incidents matching the filters.
    """
    try:
        incidents: list[IncidentRecord] = _read_incidents()
    except ValidationError:
        raise ToolFailed(
            message="Invalid incident format. Please contact support."
        ) from None
    except FileNotFoundError, PermissionError, UnicodeDecodeError:
        raise InvalidFileFormatError() from None
    upper_incs = None
    if inc_ids:
        upper_incs = {inc_id.upper() for inc_id in inc_ids}
    lower_service = None
    if service:
        lower_service = service.lower()
    filtered_by_id = (
        inc for inc in incidents if not upper_incs or inc.id in upper_incs
    )
    filtered_by_service = (
        inc
        for inc in filtered_by_id
        if not lower_service or inc.service == lower_service
    )
    filtered_by_severity = (
        inc for inc in filtered_by_service if not severity or inc.severity == severity
    )
    filtered_by_status = (
        inc for inc in filtered_by_severity if not status or inc.status == status
    )
    return list(filtered_by_status)

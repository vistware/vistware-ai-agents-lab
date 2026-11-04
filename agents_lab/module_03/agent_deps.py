from dataclasses import dataclass


@dataclass
class IncidentInvistigatorDeps:
    auth_user: str
    service: str

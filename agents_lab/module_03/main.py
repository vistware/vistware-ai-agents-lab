from decimal import Decimal

from pydantic_ai import UsageLimits

from agents_lab.module_03.agent_deps import IncidentInvistigatorDeps
from agents_lab.module_03.agents import vistware_incident_investigator
from agents_lab.module_03.dependencies import project_init
from agents_lab.module_03.schemas import UserInput
from agents_lab.module_03.tools import ServicePermissionDeniedError

AUTH_USER = "USER_02"


def get_auth_current_user() -> str:
    """Symulate auth current user retrieval."""
    return AUTH_USER


def main(input: UserInput) -> None:
    project_init()
    user_problem = (
        "After the latest deployment of service, the application started returning HTTP 500 errors."
        " Investigate what might have gone wrong and provide a diagnosis."
    )
    try:
        result = vistware_incident_investigator.run_sync(
            user_prompt=user_problem,
            usage_limits=UsageLimits(cost_limit=Decimal("2.0"), request_limit=5),
            deps=IncidentInvistigatorDeps(
                auth_user=get_auth_current_user(), service=input.service
            ),
        )
    except ServicePermissionDeniedError:
        print(f"You do not have permission to access service '{input.service}'.")
        return
    print(20 * "***")
    print("Investigation result:")
    print(result.output.model_dump_json(indent=2))
    print(20 * "***")


if __name__ == "__main__":
    main(input=UserInput(service="my_service02"))

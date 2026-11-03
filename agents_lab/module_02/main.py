from decimal import Decimal

from pydantic_ai import UsageLimits

from agents_lab.module_02.agents import vistware_incident_investigator
from agents_lab.module_02.dependencies import project_init
from agents_lab.module_02.schemas import UserInput
from agents_lab.module_02.tools import ServiceNotFoundError


def main(input: UserInput) -> None:
    project_init()
    user_problem = (
        f"After the latest deployment of service '{input.service}', the application started returning HTTP 500 errors."
        " Investigate what might have gone wrong and provide a diagnosis."
    )
    try:
        result = vistware_incident_investigator.run_sync(
            user_prompt=user_problem,
            usage_limits=UsageLimits(cost_limit=Decimal("2.0"), request_limit=5),
        )
    except ServiceNotFoundError:
        print(f"Service '{input.service}' not found.")
        return
    print(20 * "***")
    print("Investigation result:")
    print(result.output.model_dump_json(indent=2))
    print(20 * "***")


if __name__ == "__main__":
    main(input=UserInput(service="my_service"))

from agents_lab.module_01.agents import ManualVistwareIncidentInvestigator
from agents_lab.module_01.dependencies import project_init


def main() -> None:
    project_init()
    user_problem = (
        "After the latest deployment, the application started returning HTTP 500 errors."
        "Investigate what might have gone wrong and provide a diagnosis."
    )
    investigator = ManualVistwareIncidentInvestigator(user_problem=user_problem)
    result = investigator.investigate()
    print(20 * "***")
    if result is None:
        print("Investigation did not yield a conclusive result.")
    else:
        print(f"Investigation result: {result}")
    print(20 * "***")


if __name__ == "__main__":
    main()

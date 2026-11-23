import logfire
import typer
from pydantic_ai import UsageLimits
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded

from .agent_deps import IncidentInvestigatorDeps
from .agents import vistware_incident_orchestrator
from .schemas import IncidentReport
from .tools.semantic_retriever import SemanticRetriever

INCIDENT_REQUEST_LIMIT = 20
SAMPLE_QUESTIONS = (
    "What caused the JWT authentication failures after deployment?",
    "How should operators recover from the gateway rate-limiting incident?",
    "Investigate the payment processing delays, identify the confirmed root cause, "
    "and recommend recovery actions.",
    "Investigate the production incident INC-9999 and provide its confirmed root "
    "cause and resolution.",
)

app = typer.Typer()


@app.callback()
def main() -> None:
    pass


@app.command("analyze-incident", hidden=True)
@app.command("demo-incident-investigator")
def demo_incident_investigator_command() -> None:
    """Run the incident orchestrator on sample questions."""
    deps = IncidentInvestigatorDeps(knowledge_retriever=SemanticRetriever())
    for question in SAMPLE_QUESTIONS:
        typer.echo(f"Question: {question}")
        report = investigate_incident(question, deps)
        typer.echo(report.model_dump_json(indent=2))
        typer.echo("-" * 40)
        input("Press Enter to continue...")


def investigate_incident(
    question: str, deps: IncidentInvestigatorDeps
) -> IncidentReport:
    try:
        result = vistware_incident_orchestrator.run_sync(
            user_prompt=question,
            deps=deps,
            usage_limits=UsageLimits(request_limit=INCIDENT_REQUEST_LIMIT),
        )
    except UsageLimitExceeded as exc:
        typer.echo("The incident investigation reached its usage budget.", err=True)
        raise typer.Exit(code=1) from exc
    except UnexpectedModelBehavior as exc:
        typer.echo("The orchestrator could not produce a validated report.", err=True)
        raise typer.Exit(code=1) from exc
    return result.output


if __name__ == "__main__":
    logfire.configure()
    logfire.instrument_pydantic_ai()
    app()

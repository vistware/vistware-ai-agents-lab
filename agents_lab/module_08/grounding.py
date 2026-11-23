from contextvars import ContextVar
from dataclasses import dataclass

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.capabilities import WrapRunHandler
from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.run import AgentRunResult

from .agent_deps import IncidentInvestigatorDeps
from .schemas import IncidentInvestigationResult, IncidentReport, RecoveryPlan
from .tools.knowledge_search import search_knowledge


@dataclass
class _SpecialistResults:
    investigation: IncidentInvestigationResult | None = None
    recovery_plan: RecoveryPlan | None = None


_specialist_results = ContextVar[_SpecialistResults | None](
    "specialist_results", default=None
)


def remember_specialist_result(
    _ctx: RunContext[object],
    /,
    *,
    result: AgentRunResult[IncidentInvestigationResult | RecoveryPlan],
) -> AgentRunResult[IncidentInvestigationResult | RecoveryPlan]:
    results = _specialist_results.get()
    if results is not None:
        if isinstance(result.output, IncidentInvestigationResult):
            results.investigation = result.output
        elif isinstance(result.output, RecoveryPlan):
            results.recovery_plan = result.output
    return result


async def collect_specialist_results(
    _ctx: RunContext[IncidentInvestigatorDeps],
    /,
    *,
    handler: WrapRunHandler,
) -> AgentRunResult[IncidentReport]:
    # Delegated tasks inherit this state, and each orchestrator run starts fresh.
    with _specialist_results.set(_SpecialistResults()):
        return await handler()


def validate_citations(
    ctx: RunContext[IncidentInvestigatorDeps],
    output: IncidentInvestigationResult,
) -> IncidentInvestigationResult:
    search_returns = [
        part
        for message in ctx.messages
        if ctx.run_id is not None
        and isinstance(message, ModelRequest)
        and message.run_id == ctx.run_id
        for part in message.parts
        if isinstance(part, ToolReturnPart)
        and part.tool_name == search_knowledge.__name__
        and part.outcome == "success"
        and part.metadata is not None
    ]
    if not search_returns:
        raise ModelRetry("Call search_knowledge before submitting a result.")

    sources = output.supporting_sources
    if output.evidence_status != "insufficient" and (
        output.root_cause is None or not sources
    ):
        raise ModelRetry(
            "State the confirmed or suspected cause and cite at least one retrieved chunk. "
            "If the evidence is insufficient, set evidence_status to insufficient "
            "and describe the missing information."
        )

    retrieved_sources = {
        (file_path, chunk_id)
        for part in search_returns
        for file_path, chunk_id in part.metadata
    }
    if any(
        (source.file_path, source.chunk_id) not in retrieved_sources
        for source in sources
    ):
        raise ModelRetry(
            "One or more cited document paths and chunk IDs do not match a result "
            "returned by search_knowledge during this run."
        )
    return output


def validate_recovery_citations(output: RecoveryPlan) -> RecoveryPlan:
    results = _specialist_results.get()
    investigation = results.investigation if results is not None else None
    sources = investigation.supporting_sources if investigation is not None else []
    verified_sources = {(source.file_path, source.chunk_id) for source in sources}
    if any(
        (source.file_path, source.chunk_id) not in verified_sources
        for action in output.actions
        for source in action.supporting_sources
    ):
        raise ModelRetry(
            "Cite only exact document paths and chunk IDs verified by RootCauseAnalyst "
            "in this run. Use an empty source list if none supports the action."
        )
    return output


def validate_report(output: IncidentReport) -> IncidentReport:
    results = _specialist_results.get() or _SpecialistResults()
    if (
        output.investigation != results.investigation
        or output.recovery_plan != results.recovery_plan
    ):
        raise ModelRetry(
            "Copy the returned RootCauseAnalyst and RecoveryPlanner results exactly into "
            "investigation and recovery_plan. Use null for a section if its specialist "
            "did not return a result. Put your synthesis in incident_summary and limitations."
        )
    return output

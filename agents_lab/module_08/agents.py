from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import Hooks, ValidatedToolArgs
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from pydantic_ai.tools import ToolDefinition
from pydantic_ai_harness import SubAgent, SubAgents

from .agent_deps import IncidentInvestigatorDeps
from .grounding import (
    collect_specialist_results,
    remember_specialist_result,
    validate_citations,
    validate_recovery_citations,
    validate_report,
)
from .prompts import (
    INCIDENT_ORCHESTRATOR_INSTRUCTIONS,
    RECOVERY_PLANNER_INSTRUCTIONS,
    ROOT_CAUSE_ANALYST_INSTRUCTIONS,
)
from .schemas import IncidentInvestigationResult, IncidentReport, RecoveryPlan
from .settings import module_settings
from .tools.knowledge_search import search_knowledge

MAX_DELEGATED_TASK_CHARS = 4_000


vistware_root_cause_analyst = Agent(
    model=module_settings.ROOT_CAUSE_ANALYST_MODEL,
    name="RootCauseAnalyst",
    description="Vistware Root Cause Analyst for investigating incidents in Vistware services.",
    instructions=ROOT_CAUSE_ANALYST_INSTRUCTIONS,
    retries={"tools": 10, "output": 2},
    deps_type=IncidentInvestigatorDeps,
    output_type=IncidentInvestigationResult,
    model_settings=OpenAIResponsesModelSettings(
        openai_reasoning_effort=module_settings.ROOT_CAUSE_ANALYST_REASONING_EFFORT
    ),
    tools=[search_knowledge],
    capabilities=[Hooks(after_run=remember_specialist_result)],
)

vistware_recovery_planner = Agent(
    model=module_settings.RECOVERY_PLANNER_MODEL,
    name="RecoveryPlanner",
    description="Vistware Recovery Planner for preparing diagnostic and recovery recommendations for incidents in Vistware services.",
    instructions=RECOVERY_PLANNER_INSTRUCTIONS,
    retries={"output": 2},
    output_type=RecoveryPlan,
    model_settings=OpenAIResponsesModelSettings(
        openai_reasoning_effort=module_settings.RECOVERY_PLANNER_REASONING_EFFORT
    ),
    capabilities=[Hooks(after_run=remember_specialist_result)],
)

delegation_hooks = Hooks[IncidentInvestigatorDeps](run=collect_specialist_results)


@delegation_hooks.on.before_tool_execute(tools=["delegate_task"])
def validate_delegated_task(
    _ctx: RunContext[IncidentInvestigatorDeps],
    /,
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
) -> ValidatedToolArgs:
    task = args["task"].strip()
    if not 1 <= len(task) <= MAX_DELEGATED_TASK_CHARS:
        raise ModelRetry(
            f"Provide a self-contained task of 1 to {MAX_DELEGATED_TASK_CHARS} "
            "characters. Summarize only the relevant incident facts and findings."
        )
    return {**args, "task": task}


vistware_incident_orchestrator = Agent(
    model=module_settings.INCIDENT_ORCHESTRATOR_MODEL,
    name="IncidentOrchestrator",
    description="Vistware Incident Orchestrator for coordinating incident investigation and recovery planning.",
    instructions=INCIDENT_ORCHESTRATOR_INSTRUCTIONS,
    retries={"output": 2},
    deps_type=IncidentInvestigatorDeps,
    output_type=IncidentReport,
    model_settings=OpenAIResponsesModelSettings(
        openai_reasoning_effort=module_settings.INCIDENT_ORCHESTRATOR_REASONING_EFFORT,
        parallel_tool_calls=False,
    ),
    capabilities=[
        delegation_hooks,
        SubAgents(
            agents=[
                SubAgent(
                    vistware_root_cause_analyst,
                    max_calls=1,
                    resumable=False,
                    on_failure=(
                        "RootCauseAnalyst produced no result for this delegation. "
                        "Use earlier findings if available. Otherwise, report the missing "
                        "investigation findings as a limitation."
                    ),
                ),
                SubAgent(
                    vistware_recovery_planner,
                    max_calls=1,
                    resumable=False,
                    on_failure=(
                        "RecoveryPlanner produced no result for this delegation. "
                        "Use an earlier plan if available. Otherwise, report the missing "
                        "recovery plan as a limitation."
                    ),
                ),
            ],
            forward_usage=True,
            max_depth=2,
            contain_errors=True,
        ),
    ],
)

vistware_root_cause_analyst.output_validator(validate_citations)
vistware_recovery_planner.output_validator(validate_recovery_citations)
vistware_incident_orchestrator.output_validator(validate_report)

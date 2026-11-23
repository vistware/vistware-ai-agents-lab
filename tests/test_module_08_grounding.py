from collections.abc import Mapping
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic_ai import models
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.workspaces import LocalWorkspaceBackend, Workspace


def scripted_model(*replies: ToolCallPart | Mapping[str, object]) -> FunctionModel:
    responses = iter(replies)

    def respond(_messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        response = next(responses)
        if isinstance(response, Mapping):
            response = ToolCallPart(info.output_tools[0].name, dict(response))
        return ModelResponse(parts=[response])

    return FunctionModel(respond)


def test_reports_preserve_current_run_specialist_results(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    for agent in ("ROOT_CAUSE_ANALYST", "RECOVERY_PLANNER", "INCIDENT_ORCHESTRATOR"):
        monkeypatch.setenv(f"{agent}_MODEL", "openai:gpt-4o-mini")
        monkeypatch.setenv(f"{agent}_REASONING_EFFORT", "low")
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", False)

    from agents_lab.module_08.agent_deps import IncidentInvestigatorDeps
    from agents_lab.module_08.agents import (
        vistware_incident_orchestrator,
        vistware_recovery_planner,
        vistware_root_cause_analyst,
    )
    from agents_lab.module_08.tools.schemas import KnowledgeSearchResult

    source = {"file_path": "runbooks/auth.md", "chunk_id": "auth-1"}
    forged_source = {**source, "file_path": "runbooks/unrelated.md"}
    retriever = Mock()
    retriever.search = AsyncMock(
        return_value=[
            KnowledgeSearchResult(
                query="authentication",
                file_name="auth.md",
                similarity=1.0,
                content="The signing keys may have been out of sync.",
                metadata={},
                **source,
            )
        ]
    )
    investigation = {
        "incident_summary": "Authentication failed.",
        "root_cause": "The signing keys may have been out of sync.",
        "evidence_status": "suspected",
        "supporting_sources": [source],
        "missing_information": ["Key rollout timestamps."],
    }
    action = {
        "action": "Check the active signing key.",
        "action_type": "diagnostic",
        "prerequisites": [],
        "risks": [],
        "supporting_sources": [source],
        "approval_required": False,
    }
    plan = {
        "actions": [action],
        "missing_information": [],
        "unresolved_dependencies": [],
    }
    forged_plan = {
        **plan,
        "actions": [{**action, "supporting_sources": [forged_source]}],
    }
    report = {
        "incident_summary": "Authentication failed.",
        "investigation": investigation,
        "recovery_plan": plan,
        "limitations": [],
    }

    monkeypatch.setattr(
        vistware_root_cause_analyst,
        "model",
        scripted_model(
            ToolCallPart("search_knowledge", {"query": "authentication"}),
            investigation,
        ),
    )
    monkeypatch.setattr(
        vistware_recovery_planner, "model", scripted_model(forged_plan, plan)
    )

    deps = IncidentInvestigatorDeps(knowledge_retriever=retriever)
    workspace = Workspace(LocalWorkspaceBackend(tmp_path))
    result = vistware_incident_orchestrator.run_sync(
        "Investigate the authentication failures and suggest diagnostics.",
        deps=deps,
        workspace=workspace,
        model=scripted_model(
            ToolCallPart(
                "delegate_task",
                {
                    "agent_name": "RootCauseAnalyst",
                    "task": "Investigate authentication.",
                },
            ),
            ToolCallPart(
                "delegate_task",
                {
                    "agent_name": "RecoveryPlanner",
                    "task": "Plan diagnostics. Verified source: runbooks/auth.md auth-1.",
                },
            ),
            {**report, "recovery_plan": forged_plan},
            {
                **report,
                "investigation": {**investigation, "evidence_status": "confirmed"},
            },
            report,
        ),
    )

    assert result.output.model_dump() == report
    retries = [
        part
        for message in result.new_messages()
        for part in message.parts
        if isinstance(part, ToolReturnPart) and part.outcome == "retried"
    ]
    assert len(retries) == 2
    retriever.search.assert_awaited_once()

    with pytest.raises(
        UnexpectedModelBehavior, match="Exceeded maximum output retries"
    ):
        vistware_incident_orchestrator.run_sync(
            "Investigate a different incident.",
            deps=deps,
            workspace=workspace,
            message_history=result.all_messages(),
            model=scripted_model(report),
            retries={"output": 0},
        )

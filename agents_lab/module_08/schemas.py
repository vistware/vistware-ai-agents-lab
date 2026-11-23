from typing import Literal

from pydantic import BaseModel, Field


class InvestigationSource(BaseModel):
    file_path: str = Field(
        min_length=1,
        description="Exact path of the source document returned by the knowledge search",
    )
    chunk_id: str = Field(
        min_length=1,
        description="Exact ID of the retrieved chunk supporting the finding",
    )


class IncidentInvestigationResult(BaseModel):
    incident_summary: str = Field(
        min_length=1,
        description="Concise summary of the incident and its observed symptoms",
    )
    root_cause: str | None = Field(
        min_length=1,
        description="Identified or suspected root cause, or null if no cause can be identified",
    )
    evidence_status: Literal["confirmed", "suspected", "insufficient"] = Field(
        description="How strongly the available evidence supports a root cause",
    )
    supporting_sources: list[InvestigationSource] = Field(
        description="Retrieved document and chunk identifiers that support the findings",
    )
    missing_information: list[str] = Field(
        description="Information gaps relevant to the investigation",
    )


class RecoveryAction(BaseModel):
    action: str = Field(
        min_length=1,
        description="Recommended diagnostic or recovery action",
    )
    action_type: Literal["diagnostic", "recovery"] = Field(
        description="Whether the action diagnoses the incident or helps restore service",
    )
    prerequisites: list[str] = Field(
        description="Conditions that must be met before executing this action",
    )
    risks: list[str] = Field(
        description="Potential operational risks of executing this action",
    )
    supporting_sources: list[InvestigationSource] = Field(
        description="Retrieved document and chunk identifiers supporting this action",
    )
    approval_required: bool = Field(
        description="Whether approval is required before executing this action",
    )


class RecoveryPlan(BaseModel):
    actions: list[RecoveryAction] = Field(
        description="Recommended diagnostic and recovery actions in execution order",
    )
    missing_information: list[str] = Field(
        description="Information gaps that affect diagnosis or recovery",
    )
    unresolved_dependencies: list[str] = Field(
        description="Dependencies that must be resolved to proceed with the plan",
    )


class IncidentReport(BaseModel):
    incident_summary: str | None = Field(
        min_length=1,
        description="Concise incident summary, or null if no incident was described",
    )
    investigation: IncidentInvestigationResult | None = Field(
        description="Validated RootCauseAnalyst result, or null if no result was returned",
    )
    recovery_plan: RecoveryPlan | None = Field(
        description="Validated RecoveryPlanner result, or null if no result was returned",
    )
    limitations: list[str] = Field(
        description="Conflicting findings, missing context, or other limits of the report",
    )

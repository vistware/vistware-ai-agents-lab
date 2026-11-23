# Module 08 — Multi-Agent Orchestration & Delegation

**Vistware AI Agents Lab | AI Agents Engineering**

> **Educational Project — Not Production-Ready**
>
> This module explores multi-agent orchestration using Python, Pydantic AI, and Pydantic AI Harness. It demonstrates architectural patterns, specialized agent responsibilities, structured communication, execution boundaries, and evidence-based reasoning.
>
> All incident scenarios and operational documentation are fictional. The system is an educational demonstration, not an autonomous production incident-response platform. It must not be used to make or execute operational changes without appropriate verification, authorization, and human oversight.

---

## 1. Introduction

A single AI agent can perform many tasks by combining language-model reasoning with tools, external knowledge, and application services.

However, as the number of responsibilities increases, a single agent may become difficult to maintain, secure, and evaluate.

A multi-agent architecture introduces specialized agents with explicitly defined responsibilities.

Instead of expecting one model to perform every operation, an orchestrator coordinates specialists that independently solve parts of a larger problem.

A typical multi-agent system contains:

- **Orchestrator:** coordinates execution and combines specialist findings.
- **Specialists:** perform narrowly defined tasks.
- **Tools:** expose application capabilities and external information.
- **Structured contracts:** define how results move between components.
- **Execution controls:** enforce limits, access restrictions, and failure policies.

The primary architectural objective is not maximizing the number of agents. It is establishing useful boundaries between responsibilities.

## 2. Single-Agent vs Multi-Agent Architecture

A single-agent system is often preferable when tasks share the same context, use a limited toolset, and do not require distinct responsibilities or security boundaries.

A multi-agent system becomes valuable when different parts of a process require different instructions, tools, knowledge, or execution policies.

### Potential advantages

- Separation of responsibilities.
- Specialized prompts and tools.
- Reduced context for individual agents.
- Independent validation of specialist outputs.
- More explicit permissions and trust boundaries.
- Flexible delegation based on task requirements.

### Architectural costs

- Additional model requests and token consumption.
- Increased execution latency.
- More complex error handling.
- Possible information loss between agents.
- Coordination overhead.
- More opportunities for inconsistent or unsupported conclusions.

**A multi-agent architecture is justified when specialization provides measurable or operationally meaningful benefits.**

It should not be introduced merely because a framework supports it.

---

## 3. Fundamental Orchestration Patterns

### 3.1. Agent Delegation

Agent delegation allows a coordinating agent to invoke another specialized agent through an exposed tool or delegation capability.

A typical execution follows this sequence:

1. The orchestrator receives a user request.
2. It identifies a task requiring specialist expertise.
3. It delegates that task to a specialist.
4. The specialist executes independently.
5. The orchestrator receives the specialist's result.
6. The orchestrator continues reasoning or produces the final response.

The orchestrator retains responsibility for the overall task.

Delegation is especially useful when the appropriate specialist depends on the user's request.

### 3.2. Programmatic Handoff

In programmatic handoff, application code determines the execution sequence.

For example:

Root Cause Investigation → Recovery Planning → Report Generation.

The application controls which agent executes next and how results are transferred.

This approach is suitable for workflows where required stages and dependencies are known in advance.

Unlike agent-controlled delegation, the sequence does not depend entirely on model decisions.

### 3.3. Graph-Based Orchestration

Graph-based orchestration models a workflow as states and transitions.

Individual nodes may represent model calls, deterministic functions, external services, or human approval steps.

Transitions depend on explicit conditions.

Graph orchestration is particularly useful for workflows involving branches, retries, checkpoints, and complex state transitions.

It introduces additional architectural complexity and is unnecessary for many straightforward workflows.

### Choosing an orchestration pattern

| Requirement | Suitable approach |
|---|---|
| Dynamic specialist selection | Agent Delegation |
| Fixed execution sequence | Programmatic Handoff |
| Complex conditional workflow | Graph-Based Orchestration |
| Simple task using shared tools | Single Agent |

These patterns can be combined when needed.

---

## 4. Orchestrator–Worker Architecture

The educational incident investigation scenario uses one orchestrator and two specialists.

### IncidentOrchestrator

The orchestrator coordinates the investigation.

Its responsibilities include:

- Understanding the user's objective.
- Selecting appropriate specialists.
- Delegating self-contained tasks.
- Processing structured specialist results.
- Combining findings into a consistent report.
- Preserving uncertainty and evidence provenance.

The orchestrator should not duplicate specialist responsibilities unnecessarily.

### RootCauseAnalyst

This specialist investigates incident symptoms, technical failures, and possible root causes.

It can access the existing semantic knowledge retrieval mechanism developed in the previous RAG module.

Its responsibilities include:

- Retrieving relevant incident documentation.
- Comparing possible failure mechanisms.
- Distinguishing confirmed causes from hypotheses.
- Identifying missing evidence.
- Producing structured investigation findings.

### RecoveryPlanner

This specialist prepares diagnostic and recovery recommendations.

It uses investigation findings and available evidence to identify:

- Diagnostic actions.
- Conditional recovery procedures.
- Operational prerequisites.
- Potential risks.
- Actions requiring approval.

It does not execute recovery operations.

### Architectural principle

**Specialists should receive the minimum capabilities necessary to perform their responsibilities.**

For example, a recovery planning agent does not necessarily require direct access to the knowledge retrieval tool if validated investigation findings already provide sufficient context.

---

## 5. Pydantic AI Harness and SubAgents

Pydantic AI Harness provides orchestration capabilities that can simplify the implementation of multi-agent workflows.

The SubAgents mechanism supports defining and invoking specialized agents through a coordinating agent.

Important architectural considerations include:

### Delegation limits

A system should control how often specialists can be invoked.

Without appropriate limits, delegation can produce unnecessary model calls or repeated analysis.

### Delegation depth

Nested delegation increases complexity.

Limiting delegation depth helps prevent excessive chains of agents invoking other agents.

### Resumable execution

Some workflows benefit from resuming a specialist's previous execution.

Other workflows are easier to reason about when each delegation starts a fresh execution.

This is a deliberate design choice.

### Failure containment

A specialist may fail because of invalid outputs, external service failures, or model execution limits.

Failure containment allows the coordinating application to decide whether partial results remain useful.

It does not eliminate the need to handle failures that propagate outside the delegated execution.

### Usage forwarding

The system must account for model usage across the entire delegation hierarchy.

Without shared accounting, an orchestrator may underestimate the total resources consumed by its specialists.

**The framework should manage standard delegation mechanics while the application defines its own business rules, evidence requirements, and safety policies.**

---

## 6. Context Isolation and Dependency Injection

Each specialist should work with a context appropriate to its responsibility.

A specialist typically requires:

- Its own instructions.
- A clearly defined delegated objective.
- Necessary contextual information.
- Authorized application dependencies.
- Relevant tool results.

It does not automatically need the orchestrator's entire conversation history.

### Context isolation

Context isolation can improve focus, reduce unnecessary token consumption, and limit exposure to irrelevant information.

However, excessive isolation can remove information required to complete a task correctly.

The orchestrator must therefore provide enough information for a specialist to understand its delegated responsibility without depending on hidden conversation state.

### Dependency Injection

Trusted services should be provided by application code.

Examples include:

- Semantic retrievers.
- Knowledge repositories.
- Authorized service interfaces.
- Configuration and execution policies.

The language model may choose arguments for a permitted operation, but must not gain authority to change the application's trust boundaries.

### Separation of responsibilities

Model-controlled decisions may include selecting a specialist or formulating a retrieval query.

Application-controlled decisions include permissions, access to sensitive data, hard execution limits, and authorization to modify external systems.

This separation is essential for reliable agentic software.

---

## 7. Structured Communication Between Agents

Natural-language responses alone are often insufficient for reliable collaboration.

A specialist result should provide a well-defined contract that downstream components can interpret.

Pydantic models and Structured Outputs allow the application to define these contracts explicitly.

### Investigation results

A root cause analysis can represent:

- Incident summary.
- Root cause, when established.
- Evidence status.
- Supporting sources.
- Missing information.

### Recovery results

A recovery plan can represent:

- Proposed actions.
- Action categories.
- Prerequisites.
- Operational risks.
- Approval requirements.
- Supporting sources.

### Final incident report

An orchestrator may combine these results with a concise summary and known limitations.

A structured contract makes it easier to validate relationships between individual components.

However, **structural validity does not guarantee factual correctness**.

A response can satisfy its Pydantic schema while containing unsupported conclusions.

This distinction becomes particularly important when several agents exchange results.

---

## 8. Evidence Provenance and Multi-Agent Grounding

Grounding means ensuring that generated conclusions are based on available evidence.

In a multi-agent system, grounding becomes more complex because information crosses multiple execution boundaries.

A typical evidence flow is:

Knowledge Retrieval → RootCauseAnalyst → RecoveryPlanner → IncidentOrchestrator.

Each transition introduces the possibility of losing source information, changing the meaning of a finding, or introducing an unsupported claim.

### Source tracking

Retrieved chunks should have stable identifiers that can be linked to their original documents.

Specialist outputs should preserve references to the evidence used during analysis.

### Citation validation

Applications can validate whether a cited source identifier belongs to the collection of retrieved or authorized evidence.

This validation can prevent fabricated source identifiers.

However, it cannot independently establish whether the cited text supports a particular claim.

### Cross-agent consistency

An orchestrator should not present a modified specialist conclusion as though it were the specialist's original result.

Applications can preserve verified specialist outputs and compare them with the final structured report.

### Recovery recommendations

Recommendations should clearly distinguish:

- Actions grounded in documentation.
- Conditional actions requiring additional confirmation.
- General diagnostic steps.
- Unsupported or speculative suggestions.

High-risk operational actions must not be treated as authorized merely because an AI agent proposed them.

### Important limitation

**Citation validity is not equivalent to factual verification.**

A real source can be cited incorrectly. Complete factual assurance requires additional verification and evaluation mechanisms.

---

## 9. Hooks and Execution-Scoped State

Hooks allow an application to observe or extend execution at defined points.

In multi-agent orchestration, they can support operations such as:

- Initializing execution-scoped state.
- Capturing specialist results.
- Recording execution outcomes.
- Preparing data for validation.
- Cleaning up state after completion.

### ContextVar

Python's ContextVar provides context-local state for asynchronous execution.

It can help associate information with a particular logical execution without relying on a single mutable global variable.

This is useful when capturing specialist results that must later be validated by the orchestrator.

However, ContextVar does not automatically make every mutable object concurrency-safe.

When child tasks inherit context containing references to mutable objects, concurrent updates may still require explicit coordination.

### Architectural trade-off

Execution-scoped state can simplify communication between hooks and validators.

It should nevertheless have a clearly defined lifecycle and avoid leaking results between unrelated agent executions.

---

## 10. Usage Limits and Cost Engineering

Multi-agent systems can generate significantly more model requests than single-agent systems.

A single user request may trigger multiple orchestrator reasoning steps, specialist invocations, and knowledge retrieval operations.

The total cost depends on several factors:

- Number of delegations.
- Model selection for each specialist.
- Input and output token consumption.
- Size of delegated context.
- Tool execution overhead.
- Retries and failed executions.

### Shared usage accounting

The orchestration system should account for model usage across parent and child executions.

Agent-local limits are not automatically equivalent to limits over the complete workflow unless usage is explicitly shared or forwarded.

### Different models for different responsibilities

Specialists can use different model configurations.

A complex root cause investigation may require stronger reasoning capabilities than a narrower recovery planning task.

However, the cost-effectiveness of assigning different models should be determined through measurements rather than assumptions.

### Separate execution budgets

A mature system may define independent constraints for:

- Model request count.
- Token consumption.
- Number of delegations.
- Tool calls.
- Execution time.
- Monetary cost.

These limits address different risks.

For example, limiting model requests does not necessarily prevent a specialist from making several tool calls during a single model response.

---

## 11. Error Handling and Partial Results

A multi-agent system must distinguish between an unsuccessful investigation and a technical execution failure.

### Insufficient evidence

A specialist may successfully investigate an incident but find no reliable evidence establishing its cause.

This is a valid investigation outcome, not necessarily an application failure.

### Technical failure

A specialist may fail because an external service is unavailable or a model request cannot be completed.

The orchestrator should distinguish this from insufficient evidence.

### Invalid structured output

A model may return an output that does not satisfy the required contract or violates application-level validation.

The application may reject the output and request correction within configured retry limits.

### Partial reports

When some specialists succeed and others fail, an orchestrator may return a partial report if the application permits it.

The report must preserve uncertainty and must not invent missing specialist results.

### Failure handling principle

**A failed or incomplete investigation must never be silently transformed into a confirmed conclusion.**

---

## 12. Security and Human Oversight

Specialized agents should operate under least-privilege principles.

An agent responsible for investigation should not automatically have permission to execute operational recovery procedures.

Similarly, a planning agent may propose an action without having authority to perform it.

### Important controls

- Application-enforced authorization.
- Restricted tool access.
- Validation of arguments.
- Approval requirements for sensitive operations.
- Clear separation between recommendations and execution.
- Protection against prompt injection.
- Explicit handling of uncertain evidence.

A recovery recommendation involving payment processing may affect in-flight transactions, idempotency, retries, or consistency.

Such recommendations require particular caution.

The educational system produces advisory information only.

It does not execute changes in production infrastructure.

---

## 13. Multi-Agent Systems and RAG

Combining multiple agents with retrieval-augmented generation introduces an important distinction.

RAG is responsible for finding relevant external information.

Multi-agent orchestration is responsible for organizing how that information is interpreted and used.

These are complementary patterns.

A root cause specialist can retrieve evidence, identify possible causes, and produce a structured investigation result.

A recovery planner can then use the investigation result to prepare conditional recommendations.

The orchestrator combines these outputs while preserving the original evidence and limitations.

### Important considerations

- Different specialists do not necessarily need direct retrieval access.
- Information passed between agents should retain source provenance.
- Similar incidents must not automatically be treated as identical.
- Missing incident records do not prove that an incident never occurred.
- Retrieval similarity does not establish causal correctness.

A multi-agent system should preserve the distinction between what the documentation establishes and what the model merely considers plausible.

---

## 14. Architectural Trade-offs and Production Considerations

The educational architecture demonstrates several important patterns, but production multi-agent systems require additional engineering.

Potential production concerns include:

- Persistent workflow state.
- Recovery after process interruptions.
- Strong authentication and authorization.
- Tenant isolation.
- Concurrency-safe execution state.
- Distributed tracing and observability.
- Latency and cost budgets.
- Operational approval workflows.
- Systematic agent evaluations.
- Versioning of prompts and model configurations.
- Monitoring for degraded answer quality.
- Reliable handling of external service failures.

Not every application requires all these mechanisms.

The appropriate architecture depends on the workload, risk level, scale, and operational requirements.

### Why this project remains educational

The project intentionally focuses on understanding orchestration, delegation, structured communication, and evidence validation.

It uses fictional incidents and simplified execution boundaries.

It does not claim to provide independently verified incident diagnoses or autonomous recovery capabilities.

---

## 15. Key Engineering Takeaways

1. Multi-agent systems should introduce meaningful specialization, not unnecessary complexity.
2. Orchestrators coordinate tasks; specialists perform focused responsibilities.
3. Agent-controlled delegation and deterministic handoff solve different problems.
4. Structured Outputs improve communication but do not guarantee factual accuracy.
5. Evidence provenance must survive communication between agents.
6. Context isolation helps control information exposure and token consumption.
7. Trusted dependencies and authorization must remain under application control.
8. Execution budgets should cover the complete delegation hierarchy.
9. Failures and insufficient evidence must be represented explicitly.
10. Existing orchestration frameworks should be reused when they meet the application's requirements.

**The central principle of multi-agent engineering is controlled collaboration: specialized agents contribute independent capabilities while application code maintains trustworthy boundaries, resource constraints, and output validation.**

---

*Vistware AI Agents Lab — Educational exploration of multi-agent orchestration with Python and Pydantic AI.*

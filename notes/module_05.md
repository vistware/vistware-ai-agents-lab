# Module 05 — Error Handling and Recovery in Pydantic AI

> **Vistware AI Agents Lab · Theoretical learning notes · Python 3.14 / Pydantic AI**
>
> This chapter explains the behavior and design choices demonstrated in Module 05. It is a conceptual guide, not an implementation tutorial.

## 1. Purpose of the Module

An AI agent does not encounter only ordinary application errors. It also receives model-generated arguments, calls tools, interprets tool outcomes, and may continue reasoning after an operation fails. Error handling therefore requires a decision about **who should respond to a failure**: the model, the agent runtime, or the application.

Module 05 focuses on distinguishing three outcomes:

- **Correction:** the model receives feedback and can attempt another action.
- **Reported failure:** the model learns that an operation failed and may adapt its answer or strategy without being explicitly instructed to retry.
- **Termination:** an exception leaves the agent execution path, and the application handles the failure.

These outcomes serve different purposes. They should not be collapsed into a single generic recovery strategy.

## 2. Where Errors Can Occur

Failures can originate at different boundaries:

| Boundary | Nature of failure | Primary responsibility |
| --- | --- | --- |
| Model → tool | Invalid or unsupported generated arguments | Framework validation and tool contract |
| Inside a tool | A tool cannot complete the requested operation | Tool implementation and chosen failure policy |
| External data → application | Source records cannot be validated | Data-integrity policy |
| Application → operating system | Missing resource, denied access, or decoding failure | Application and infrastructure |
| Model → final output | Generated response does not satisfy the output contract | Framework output validation |
| Runtime → model provider | Provider error, timeout, or rate limit | Transport/provider retry policy or application termination |

Identifying the boundary matters because a language model may be able to correct its own arguments but cannot necessarily repair a corrupt source file or missing operating-system permissions.

## 3. `ModelRetry`: Feedback That Invites Correction

`ModelRetry` is a Pydantic AI exception used to send corrective feedback to the model. It tells the agent runtime that the previous tool attempt was not acceptable and that the model can make another decision based on the supplied reason.

Key properties:

- The model receives a failure message as part of its working context.
- It may revise arguments, choose a different action, or attempt the tool again.
- The configured **tool retry budget** applies.
- A retry is a further model-driven decision, **not** necessarily an identical low-level HTTP request.
- Further calls can increase latency and token usage.

In Module 05, `ModelRetry` is triggered by a **deliberately randomized condition**. This is an educational fault-injection technique designed to make retry behavior observable; it is not presented as a model-generated mistake or a recommended production strategy for recovering from transient infrastructure failures.

The specific retry message should communicate the nature of the simulated failure rather than misattribute its cause to the model.

## 4. `ToolFailed`: Report the Failure Without Consuming Tool Retries

`ToolFailed` communicates that a tool failed, while allowing the agent to take that information into account when deciding what to do next.

Unlike `ModelRetry`, `ToolFailed` **does not consume the tool's retry budget**. It also does not necessarily terminate the agent run. The model may stop with an appropriately qualified response, choose another path, or make another call if the overall execution limits permit it.

This distinction is important:

| Question | `ModelRetry` | `ToolFailed` |
| --- | --- | --- |
| Does the model learn about the failure? | Yes | Yes |
| Does it explicitly invite correction? | Yes | No |
| Does it consume the tool retry budget? | Yes | No |
| Does it automatically terminate the entire run? | No | No |
| Can subsequent model steps consume tokens? | Yes | Yes |

A reported tool failure is not the same as an empty but successful search result. The two carry different meanings for any later analysis.

## 5. Ordinary Exceptions: Stop Agent Execution

Ordinary Python exceptions raised from tools normally propagate out of Pydantic AI agent execution unless another layer handles them. They are suitable when the application deliberately requires the run to stop rather than leaving recovery to the model.

Module 05 defines an application-specific exception, **`InvalidFileFormatError`**, for system-level inability to read the CSV source. The demonstrated handling groups these conditions under one domain-facing failure:

- `FileNotFoundError`: the source file is unavailable at read time.
- `PermissionError`: the process cannot access the file.
- `UnicodeDecodeError`: the file bytes cannot be decoded using the expected text encoding.

The chosen policy is **fail-fast**: do not ask the model to compensate for a source that the application cannot reliably read.

An important boundary detail: a Pydantic `FilePath` setting can reject a missing path during settings initialization, before the tool executes. Such a failure occurs in configuration validation rather than inside the CSV-reading tool.

## 6. Deliberate Error Policy in the Lab

The module intentionally does **not** treat every invalid CSV-related condition as fatal. Its distinctions are an explicit architectural choice:

| Condition | Deliberate mechanism | Intended behavior |
| --- | --- | --- |
| Simulated intermittent tool failure | `ModelRetry` | Let the model observe and potentially retry |
| Invalid incident record detected by Pydantic | `ToolFailed` | Inform the model that the current dataset could not be validated |
| File unavailable, unreadable, or inaccessible | `InvalidFileFormatError` | Terminate the run through an application exception |

The second row is particularly important. A Pydantic `ValidationError` while parsing incident records is **deliberately translated into `ToolFailed`**. It is not accidentally left uncaught and it is not being represented as a successful read.

This lets the lesson demonstrate how the agent responds to unavailable current evidence. The system-level conditions follow a separate, intentional termination path. These are the boundaries of this training module, not a universal policy for every application.

## 7. Argument Validation vs. Source Validation

Pydantic AI derives tool argument schemas from Python type annotations and supported Pydantic constraints. Errors in model-provided arguments can be detected before a function body runs, and the framework may provide validation feedback so the model can correct its call.

That is distinct from validating records **after** the tool has accessed the CSV source. A schema error in an incident record is a problem with external input data, not necessarily a mistake in the tool arguments selected by the model.

Keep the two responsibilities separate:

- **Tool-input contract:** what arguments the model is allowed to submit.
- **Source-data contract:** what constitutes a valid incident record supplied by the CSV.

The mere presence of Pydantic on both sides does not imply that the recovery behavior should be identical.

## 8. Retry Budgets and Execution Limits

Pydantic AI distinguishes correction budgets from broader usage limits.

**Retry configuration** controls how many attempts may be made to correct tool or output failures under the relevant retry policy. Module 05 configures `retries=10` at the agent level to make those mechanisms easier to observe. This is a maximum correction budget, not an instruction to execute exactly ten retries.

**Usage limits** constrain resource consumption, including model requests and estimated cost. Module 05 also configures a request limit and a cost limit. Consequently, agent execution can stop because of a usage limit **before** an individual tool's retry allowance is exhausted.

Two outcomes must not be confused:

- The **model decides to finish** after learning about a failure and returns a structured answer.
- The **runtime stops execution** because a retry or usage limit is exhausted, potentially raising an exception.

A final structured answer containing a support recommendation is not evidence by itself that the complete retry budget was consumed.

## 9. `ToolFailed` and Conversation Memory

Module 05 also demonstrates an interaction with the earlier conversation-memory module.

The agent had access to an existing conversation and encountered a failure while attempting to validate the current CSV data. It used earlier conversational findings as historical context and explicitly qualified them as **potentially outdated**, because the latest read could not verify them.

This observation illustrates two complementary principles:

1. Conversation history can preserve earlier findings and help the agent continue an analysis.
2. Historical findings are **not** equivalent to successfully refreshed source data.

In particular, a failure message and a previously observed incident list can coexist in the same conversational context. The agent should not present old records as if it had just confirmed them.

The behavior was observed in the training experiment, but the distinction between *previously known* and *currently verified* data remains a responsibility that applications must model deliberately when needed.

## 10. Handling Output Failures

Tool errors are only part of the picture. An agent can also generate a final response that violates the configured output contract.

Pydantic AI uses output validation and corresponding correction mechanisms. Tool retries and output retries are distinct concerns, even when an agent-level configuration provides defaults for both.

A structurally valid Pydantic result does not necessarily mean that its factual claims are accurate. Structural validation and evidence-based assessment solve different problems.

## 11. Agent Retries vs. Transport Retries

These should be understood as different layers:

- **Agent-level correction:** a model sees feedback and can change its next action.
- **Transport/provider retry:** a client or transport may repeat an HTTP request after a recoverable communication failure.

Both can influence latency, resource usage, and completion behavior. They should not be assumed to share the same counter or meaning.

For state-changing tools, repeated execution also raises idempotency concerns. That topic is intentionally outside this read-only CSV module.

## 12. What Module 05 Intentionally Does Not Cover

Module 05 is a focused educational demonstration, not an operational error-handling platform. Its scope explicitly excludes:

- Automated test suites and evaluation frameworks; these belong to a separate training block.
- Production-grade transport retry and backoff orchestration.
- Self-healing or automatic modification of invalid source records.
- Database transactions, distributed recovery, and idempotency infrastructure.
- Full alerting, incident-management integration, and production observability.

The randomized failure is intentional fault injection for learning. The error policy is intentional. The small read-only dataset is intentional. None of these choices should be mistaken for unnoticed gaps.

## 13. Key Takeaways

**`ModelRetry`** is feedback that allows the model to attempt a correction and consumes the applicable tool retry budget.

**`ToolFailed`** reports an unsuccessful tool operation to the model without consuming that retry budget, and it does not automatically stop the agent.

**Ordinary application exceptions** can terminate execution when a failure must be handled outside the model's decision loop.

**Validation of generated tool arguments** is different from **validation of external source records**.

**Conversation memory** can support continuity during failure, but it must not turn previous findings into claims of fresh verification.

**Retry limits and usage limits** are distinct mechanisms that may end a run for different reasons.

The central engineering skill is choosing the right failure semantics for the boundary where the problem occurred, rather than applying retries indiscriminately.

## Further Reading

- [Pydantic AI — Retries](https://pydantic.dev/docs/ai/core-concepts/retries/)
- [Pydantic AI — Advanced Tools and Toolsets](https://pydantic.dev/docs/ai/tools-toolsets/tools-advanced/)
- [Pydantic AI — Agents and Usage Limits](https://pydantic.dev/docs/ai/core-concepts/agent/)
- [Pydantic AI — Message History](https://pydantic.dev/docs/ai/core-concepts/message-history/)

---

*Vistware AI Agents Lab — an educational exploration of AI agent engineering. The source code in the module provides the practical demonstration; this document provides the conceptual foundation.*

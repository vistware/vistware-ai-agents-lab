# Module 03 — RunContext, Dependency Injection, and Trust Boundaries

**Vistware AI Agents Lab · Python 3.14 · Pydantic AI**  
**Format:** Theory-only learning guide  
**Audience:** Python developers and software engineers

> This chapter explains the architecture and design principles behind dependency injection and execution context in Pydantic AI. It deliberately contains no implementation walkthroughs, code snippets, or exercises. The repository's source files provide the separate practical material.

## Learning objectives

After reading this chapter, you should understand:

- What dependency injection means in an AI agent runtime.
- What `RunContext` represents and what it does **not** represent.
- The distinct responsibilities of `deps_type`, `deps`, and `ctx.deps`.
- The difference between application-controlled context and model-generated tool arguments.
- How typed dependencies can support authorization and tenant isolation.
- Which execution metadata is available and why it should be used selectively.
- The limits of prompts, validation, and dependency injection as security controls.

## 1. Why agents need dependency injection

A language model can select actions, but it cannot independently establish a trustworthy identity, own a database connection, or decide which customer records an application is authorized to expose. Those responsibilities belong to the application.

An agent's tools typically need access to services and runtime data: repositories, HTTP clients, monitoring interfaces, user identity, permissions, configuration, and other resources. Dependency injection makes these objects available explicitly, instead of relying on hidden global state or embedding privileged data in the model's instructions.

In Pydantic AI, dependency injection is designed to work with ordinary Python types. The dependencies can be grouped into a typed container, supplied when an agent run begins, and accessed by selected parts of the agent runtime.

This enables two useful forms of separation:

1. **Decision-making versus execution.** The model decides which permitted capability is useful; application code decides how that capability is carried out.
2. **Untrusted input versus trusted execution context.** A model's proposed arguments are handled differently from identity and authorization context established by the application.

Dependency injection is an architectural technique, not an authorization system by itself.

## 2. Three concepts that must not be confused

### `deps_type`: the expected type

`deps_type` declares the expected shape of dependencies for a particular agent. Its primary purpose is type safety: it lets static analysis and developer tooling understand what the agent's tools and context-aware functions expect.

It is **not** a service container that automatically creates dependencies. It does not retrieve a user from an identity provider or initialize network clients on its own.

### `deps`: the supplied instance

`deps` is the actual object provided when an agent run begins. It can contain values and services that have already been created by the application.

Because it is supplied per run, separate executions can use the same agent definition while receiving different application contexts. The application must manage the lifetime, validity, and trustworthiness of the supplied objects.

### `ctx.deps`: access during execution

`ctx.deps` is the access path used by context-aware functions while the agent runs. Its type follows the dependency declaration associated with the agent.

It does not imply that all dependency values are sent to the model. A dependency remains an application-side object unless a tool, a dynamic instruction, or another deliberate integration exposes information derived from it.

| Concept | Primary responsibility | Controlled by |
|---|---|---|
| `deps_type` | Declare the dependency contract | Developer |
| `deps` | Provide concrete dependencies for a run | Application |
| `ctx.deps` | Access those dependencies during a run | Pydantic AI runtime and application code |

## 3. What is `RunContext`?

`RunContext` is a typed object that provides access to information about the **current agent execution**. It combines the application's injected dependencies with operational state supplied by the framework.

It is not synonymous with the conversation history and is not merely a collection of arbitrary function parameters.

Its responsibilities fall into three conceptual categories.

### 3.1 Application dependencies

The dependency object may expose application-managed services, configuration, user identity, scope, and other context needed to perform an operation.

The key principle is that the **application supplies these values**. The model should not be trusted to declare its own identity or assign itself additional privileges.

### 3.2 Execution state

The context can expose information associated with the current run, including details about the model, current step, usage, and configured limits. These fields make runtime-aware instrumentation and control possible.

Execution metadata is not the same as durable state. A single run can end while an application's business workflow continues elsewhere.

### 3.3 Tool-call metadata

When available for a tool invocation, the context can expose the tool's identity, call identifier, and retry-related information. This is useful for understanding what is happening within the agent's execution loop.

Not every property is meaningful or populated in every callback. Consult the API reference and treat optional fields accordingly.

## 4. Execution context is not conversation memory

These concepts frequently appear together, but they solve different problems.

**Run context** describes the present execution and gives application code access to dependencies and runtime metadata.

**Conversation history** records previous messages and potentially tool-related exchanges that the agent can use to continue a conversation. Whether that history persists between runs depends on the application's chosen history or persistence strategy.

**Application state** is the system's authoritative record of durable facts, operations, permissions, and outcomes. It may outlive any single model request, tool call, or agent run.

An agent should not treat remembered text as a replacement for authoritative application data. The presence of a statement in conversational history does not make it an authenticated fact.

## 5. Tool arguments versus injected dependencies

This is the central architectural distinction of the module.

A tool argument may be chosen by the model, subject to the tool's declared schema and validation rules. It expresses what the model is asking the application to do.

An injected dependency is prepared by the application. It expresses facts and capabilities that the model is not entitled to invent or redefine.

For reliable agent systems, separate the following concerns:

| Concern | Appropriate owner |
|---|---|
| Choosing a relevant diagnostic operation | Model, within the available toolset |
| Selecting a bounded query or result count | Model, subject to validation and limits |
| Authenticating the caller | Application and identity infrastructure |
| Determining tenant membership | Application and authorization layer |
| Determining which resources the caller can access | Application and authorization layer |
| Establishing API/database clients | Application and infrastructure |
| Enforcing read/write permissions | Tool/service implementation |
| Generating a summary of retrieved evidence | Model, with output validation and oversight |

A tool signature and the presence of `RunContext` provide the interface for this separation. They do not automatically enforce correct permissions; that enforcement has to exist in the underlying implementation.

## 6. Context-aware tools and plain tools

Pydantic AI supports both context-aware and context-free functions as tools.

**Context-aware tools** receive `RunContext` and can use injected dependencies or runtime metadata. They are appropriate when an operation needs application-specific state or services.

**Plain tools** do not receive `RunContext`. They are appropriate when the operation only needs its ordinary arguments and has no reason to access the current run's dependencies.

The distinction affects the function's contract, not its level of intelligence. Both types are exposed to the model through the tool mechanism, and both can return structured information.

During tool registration, Pydantic AI can inspect function signatures and documentation to derive model-visible tool schemas. The context parameter itself is not exposed as a model-generated argument.

**Design principle:** use the least amount of context a tool actually needs. Adding context to every function may increase coupling without improving correctness.

## 7. Type safety and the role of generics

Pydantic AI associates an agent's dependencies with a generic type. Matching the expected type across the agent and its context-aware functions enables static type checkers to validate access to injected objects.

This can catch mistakes such as using the wrong dependency type or assuming a field exists when it does not.

However, type checking is not the same as runtime authorization. A correctly typed value may still represent an unauthorized user, an expired credential, or an invalid resource selection.

The responsibilities remain distinct:

- **Static typing:** whether the program's declared interfaces are consistent.
- **Runtime input validation:** whether values satisfy the operation's constraints.
- **Authentication:** who initiated the operation.
- **Authorization:** what that identity is permitted to access or change.
- **Business validation:** whether the requested action is allowed by domain rules.

Strong agent engineering requires all of the relevant layers, not one layer pretending to replace the others.

## 8. Multi-tenant isolation and authorization

Multi-tenant systems have a particularly important trust boundary: one customer's data must not become visible to another customer because a language model proposed a different identifier.

The model's proposed tool call must not serve as the source of truth for tenant identity or permissions.

A robust design places identity and authorization decisions within trusted application code. Each data-access operation must enforce the applicable scope before returning information. The relevant boundary is the protected resource, not merely the text of the prompt.

Using dependencies to carry established identity and scope is a useful design pattern because it keeps privileged values out of the model-selected argument list. But the dependency object is only as trustworthy as the code that constructed it.

There are additional concerns beyond the immediate tutorial scope: request authentication, policy changes, revocation, row-level access, service-to-service authorization, auditability, and preventing cross-request state leakage.

**Key rule:** never equate a model's stated intent with permission to execute an operation.

## 9. Prompt injection and data exposure

Prompt injection occurs when untrusted content attempts to redirect the model's behavior or override higher-priority instructions. Logs, retrieved documents, tool results, and external messages can all carry such content.

Keeping privileged identity and permissions in application-side dependencies reduces the need to disclose them to the model. This supports a clearer trust boundary, but it does **not** eliminate prompt injection risk.

Two distinctions matter:

- A value placed in a prompt is not automatically an attack. The risk depends on its provenance, content, and how the application treats it.
- A value held in `deps` is not automatically protected from disclosure. A tool or dynamic instruction can still expose it to the model, intentionally or accidentally.

Effective defense requires restricted capabilities, authorization in code, controlled tool outputs, secret handling, input boundaries, and oversight of risky operations. Prompt wording alone is not a security boundary.

## 10. Model-visible schemas and validation

Pydantic AI uses type information to describe tool inputs and validate model-proposed arguments before calling Python functions. Constraints attached to types can communicate and enforce supported ranges and shapes.

This matters because a parameter being *typed* does not necessarily mean every value of that type is safe. A valid integer may still be negative, unreasonably large, or incompatible with domain requirements.

Validation should be applied at the right layer:

- Tool argument constraints validate the immediate model-to-tool boundary.
- Domain validation protects business invariants.
- Authorization protects resource access.
- Infrastructure controls manage resource consumption and external side effects.

No single schema can substitute for all of these controls.

## 11. Execution metadata and observability

`RunContext` can expose operational information useful for logging and tracing, such as the current execution step, usage information, tool identity, and retry-related state.

This metadata helps explain **how** an agent arrived at a result. It can support investigation of repeated tool calls, expensive execution paths, unexpected failures, and decisions that require human review.

Observability should not be confused with logging everything. Operational instrumentation should be designed around useful questions while minimizing sensitive data exposure.

A minimal educational agent need not consume every available metadata field. Removing unused instrumentation after learning what it does can be a sound design choice.

## 12. Dependency lifetime and concurrency

Agent definitions and per-run dependencies have different lifetimes. An application may reuse an agent definition while supplying separate dependencies for distinct invocations.

The lifecycle of injected clients and resources remains the application's responsibility. Network connections, transactional scopes, request-specific identity, and mutable caches need explicit ownership and cleanup rules.

Concurrency creates another requirement: mutable state belonging to one execution must not leak into another. Sharing a single agent definition does not mean that every run should share the same mutable dependency object.

Pydantic AI supports synchronous and asynchronous tools. The appropriate choice depends on the I/O and execution characteristics of the dependencies, not simply on whether the agent is invoked through a synchronous convenience method.

## 13. Errors and authorization failures

An invalid model-generated argument, an inaccessible resource, a network failure, and an internal programming defect are different classes of failure.

These distinctions matter because they imply different responses:

- A malformed model argument may be correctable without ending the whole workflow.
- A denied permission should be enforced by the application; the model should not be able to negotiate its way around the restriction.
- A transient infrastructure failure may warrant a bounded retry.
- An unexpected programming error should remain diagnosable rather than being silently converted into a plausible-looking agent answer.

Pydantic AI provides mechanisms for error feedback and retry behavior, but the decision about what is recoverable must follow the application's domain and security rules.

## 14. What dependency injection does not solve

Dependency injection improves structure, typing, and control over how an agent reaches application resources. It does not, by itself, provide:

- Authentication or authorization.
- Conversation persistence or durable workflow state.
- Guaranteed protection against prompt injection.
- Correctness of model-generated diagnoses.
- Secure handling of every external integration.
- Automatic cleanup of arbitrary injected resources.
- Complete observability or evaluation of agent quality.

These capabilities require additional design, code, and operational controls.

## 15. Intentional scope of this educational module

This module demonstrates the mechanics and architectural implications of `RunContext` and dependency injection. It is **not** presented as a production-ready identity, access-control, or incident-management system.

The author is aware of the broader requirements for a deployable system, including validated identity, policy enforcement, tenant isolation, secret management, bounded resource access, handling of external failures, auditing, and safe lifecycle management.

The educational implementation intentionally keeps these concerns small enough to make the responsibility boundary easy to understand. Readers should not interpret a simplified authorization decision or synthetic diagnostic data as a recommended production security architecture.

Automated testing, systematic evaluation, and durable execution are important topics, but are outside this module's theory-only scope and can be studied separately.

## 16. Core takeaways

1. **The model proposes actions; the application remains responsible for authority and execution.**
2. **`deps_type`, `deps`, and `ctx.deps` describe different parts of the dependency-injection contract.**
3. **`RunContext` combines injected dependencies with information about the current agent run.**
4. **Tool arguments must not be confused with trusted user identity or permissions.**
5. **Typing, validation, authentication, and authorization solve different problems.**
6. **Dependency injection supports trust boundaries but does not replace security enforcement.**
7. **Use runtime metadata and complexity only when they serve a clear engineering purpose.**

---

## Further reading

- [Pydantic AI — Dependencies](https://pydantic.dev/docs/ai/core-concepts/dependencies/)
- [Pydantic AI — Function Tools](https://pydantic.dev/docs/ai/tools-toolsets/tools/)
- [Pydantic AI — RunContext API reference](https://pydantic.dev/docs/ai/api/pydantic-ai/tools/)
- [Pydantic AI — Agents](https://pydantic.dev/docs/ai/core-concepts/agent/)

---

**Vistware AI Agents Lab**  
*Understand the runtime. Keep trust boundaries explicit. Engineer with intention.*

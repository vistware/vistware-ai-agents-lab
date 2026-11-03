# Module 02 — Understanding Pydantic AI

> **Vistware AI Agents Lab** · Python 3.14 · Theory guide  
> **Focus:** agent architecture, framework-managed execution, typed tools, structured results, and engineering responsibilities.

## About this guide

This chapter explains **how Pydantic AI works and why its abstractions exist**. It is written for developers who want to understand the design of agentic applications before implementing their own systems.

The chapter is intentionally **theory-only**. It contains no code samples, implementation walkthroughs, fictional incidents, practical exercises, or solution templates. The corresponding source code lives separately in the repository.

Pydantic AI is an agent framework for Python. Its main value is not making a language model intelligent; it is providing a typed application layer around model interactions and tool execution. The framework manages common mechanics while leaving business rules, security boundaries, and operational decisions with the developer.

---

## 1. From a language model to an agent

A **language model** receives input and produces output. It has no inherent authority to read private databases, invoke local functions, or change application state. Those abilities exist only when software explicitly makes them available.

An **agentic application** combines a model with instructions, tools, execution control, and a way to interpret results. The model may help decide the next action, but the hosting application determines what actions are possible and under what conditions they are allowed.

The **agent runtime** coordinates the interaction. It passes context to the model, processes tool requests, executes registered functions, returns their results, and determines when an acceptable final output has been produced or execution must stop.

An agent is therefore not merely a prompt or a model instance. It is a controlled software process with probabilistic decisions inside it.

## 2. Why use an agent framework?

Without a framework, application code must coordinate model requests, tool definitions, argument handling, tool execution, conversation continuity, retries, and final-result validation.

Pydantic AI provides reusable mechanisms for these responsibilities. This reduces duplicated orchestration code and gives a consistent vocabulary for working with models and tools.

The framework does **not** remove the need to design domain boundaries, authorization, error policies, observability, or safeguards. In particular, a framework-validated response is not automatically a factually correct or safe response.

### Manual orchestration versus framework orchestration

| Responsibility | Manual agent loop | Pydantic AI |
| --- | --- | --- |
| Model communication | Application implements the API workflow | Model integration is abstracted |
| Tool descriptions and schemas | Application prepares them | Derived from registered tools |
| Tool dispatch | Application interprets and routes requests | Framework manages registered function tools |
| Tool argument validation | Application designs the validation pipeline | Schema-based validation is integrated |
| Final output | Application interprets model text | Declared output types are validated |
| Conversation state | Application implements continuity | Message history and conversation mechanisms are provided |
| Execution limits | Application counts and enforces limits | Usage-limit mechanisms are available |
| Business rules and permissions | Application-owned | Still application-owned |

The trade-off is deliberate: framework abstractions make ordinary workflows more consistent, while some low-level provider behavior becomes less visible unless tracing and inspection are used.

## 3. The Agent abstraction

An **Agent** is the central configuration and execution abstraction. It brings together the model, behavioral instructions, registered tools, expected output contract, model settings, and runtime behavior.

An agent definition describes **how a task may be handled**. An individual run represents **one execution of that definition**. A single agent definition may be invoked many times with different input, dependencies, and conversational context.

This distinction is important. State belonging to a specific user, tenant, or execution should not be confused with static configuration shared by every run.

### Agent metadata

Agent names and descriptions are useful for identification, diagnostics, and integration. A description attached to the agent should not be treated as a substitute for behavioral instructions. Whether metadata becomes visible to a model depends on the surrounding orchestration, not merely on its presence in an agent declaration.

## 4. How the execution loop works

The runtime repeatedly coordinates the model and the application until the agent can return a final result or execution is interrupted.

At a conceptual level, an execution has these possible phases:

1. Assemble the active instructions, user input, message history, and available tool definitions.
2. Request the model's next response.
3. Interpret the response as a final-result candidate, a tool request, or another framework-supported outcome.
4. Validate any requested tool arguments and execute the selected tools under application control.
5. Deliver tool results back into the model-facing conversation.
6. Continue or stop according to the model's response and the runtime's constraints.

The model **requests** tools; it does not directly execute Python functions. Tool execution occurs in the application environment. This separation is one of the most important security boundaries in agent engineering.

The sequence is not a guarantee that every request will involve tools. A model may produce a final result without calling any function, unless additional application logic enforces a stricter process.

## 5. Tools: the boundary between model decisions and software behavior

A **tool** exposes a narrowly defined capability to an agent. Its name, description, input contract, and returned data form the model-facing interface.

Pydantic AI can derive tool argument schemas from Python function signatures and type annotations. It can also extract descriptions from docstrings. Descriptions help a model select and use a tool; they do not grant permission or provide a security guarantee.

### Registration and context

Tools must be explicitly registered with an agent or an associated toolset. The framework does not grant access to every function available in the Python environment.

Two common forms of function tools are distinguished by whether they receive **RunContext**:

- **Context-free tools** operate on their declared parameters without a runtime context argument.
- **Context-aware tools** receive the current execution context, including application-provided dependencies.

The choice should reflect actual dependencies. Context should not be added merely to satisfy the style of an API; nor should sensitive dependencies be turned into model-selectable parameters without a security reason.

### Tool contracts

A useful tool contract specifies not only types, but also constraints, semantics, and failure behavior. Type annotations by themselves cannot express every business rule. Input constraints, domain validation, and authorization must still be enforced by trusted application code.

Tool responses are **data**, not authoritative instructions. Logs, documents, external API payloads, and other retrieved content may contain malicious or misleading text. Returning them through a framework does not make that content trustworthy.

## 6. Structured outputs and Pydantic validation

A **structured output** declares the shape of the final answer expected from the agent. Pydantic AI uses the declared output contract to validate model-produced data and, where supported, communicate the structure to the model provider.

A well-defined output contract makes downstream processing safer and clearer. It separates the application's expected data format from the model's free-form language generation.

However, **schema validity is not factual validity**. A result can conform to every declared field and still contain an unsupported diagnosis, incorrect conclusion, or misleading certainty. Domain checks and independent evidence review remain separate responsibilities.

### Final result versus tool request

A crucial distinction is that a tool request is part of the **execution protocol**, while a structured output is the **result contract**. Pydantic AI handles ordinary tool-calling control flow internally. The final output type should describe what the calling application needs after the agent finishes, rather than reimplementing the framework's internal tool dispatch protocol.

## 7. Instructions versus system prompts

Pydantic AI supports both **instructions** and **system prompts**. Both can influence model behavior, but they have different relationships with message history.

- **Instructions** represent the current agent's active behavioral guidance. When prior message history is reused, the framework uses the current agent's instructions rather than carrying over older agents' instructions as active guidance.
- **System prompts** are represented in the conversation history and may therefore remain present when that history is reused or transferred.

The Pydantic AI documentation recommends **instructions** for most use cases. System prompts are appropriate when preserving instruction-like content in conversation history is a deliberate requirement.

Instructions may be static or evaluated at runtime. Dynamic instructions are useful when trusted runtime state must affect how the agent works. Untrusted retrieved content must not be promoted into authoritative instructions.

Neither mechanism replaces input validation, access control, or tool-level authorization.

## 8. Model settings and reasoning effort

A model's behavior depends on both the selected model and its request settings. Pydantic AI provides common settings as well as provider-specific settings.

**Reasoning effort** determines how much reasoning work the provider is asked to allocate, where that capability is supported. Higher effort may improve difficult decisions, but can increase latency and token consumption. It does not guarantee correctness.

Pydantic AI offers a provider-neutral **thinking** configuration and model-provider-specific settings such as OpenAI's reasoning effort. The provider-specific setting takes precedence when both mechanisms apply. Supported values and exact behavior depend on the selected model.

Model selection, reasoning settings, response structure, and tool access should be treated as separate design decisions. More reasoning is not a substitute for better data or better-defined tool contracts.

## 9. RunContext and dependency injection

**RunContext** is the framework's representation of information available during a particular agent execution. It can expose application dependencies and operational information about the current run.

**Dependency injection** allows the application to supply trusted objects at execution time without asking the model to choose or construct them. The dependency type describes what is expected; the runtime receives actual dependency instances supplied by the application.

The distinction between **model-controlled inputs** and **application-controlled dependencies** is fundamental:

- Model-controlled inputs are subject to model error, ambiguity, and manipulation.
- Application-controlled dependencies can carry access-controlled resources and trusted state.

Sensitive values and authorization decisions should remain on the application side of this boundary. RunContext makes dependencies accessible to trusted tool code; it does not automatically disclose them to the model.

RunContext is distinct from conversation memory. It describes execution context and related metadata, not simply a transcript.

*A dedicated later module covers RunContext, typed dependencies, lifecycle, and boundary enforcement in depth.*

## 10. Message history and conversation continuity

Within a run, the runtime maintains the messages required to coordinate model interactions and tool results. Across runs, continuity must be managed explicitly by the application using the framework's supported history or conversation mechanisms.

**Message history** concerns the records of interactions. **Conversation state** may include additional information such as identifiers, usage tracking, and deferred work. These concepts overlap but are not identical.

Keeping context has benefits and costs. It allows the model to build on earlier observations, but can increase token consumption, propagate earlier mistakes, and expose irrelevant information if context is shared too broadly.

Conversation boundaries should follow user, task, and tenant boundaries. Historical context must not be treated as universally safe to reuse.

## 11. Asking users for information

An agent may identify missing information and produce a clarification request. That does **not** mean the framework automatically owns a user interface or knows where to collect the reply.

The application remains responsible for presenting a question, capturing a user response, associating it with the correct conversation, and resuming the appropriate workflow.

Synchronous interaction through a blocking process input and a durable human-in-the-loop workflow are different architectural choices. Durable approval, suspension, and resumption require explicit lifecycle design.

For critical required inputs, relying solely on natural-language instructions is insufficient. The application should also enforce the requirements that matter for correctness or access control.

## 12. Errors, retries, and recovery

Agentic systems encounter several fundamentally different failure classes:

- **Model-output failures:** the response violates a required structure or cannot be interpreted.
- **Tool-input failures:** the model proposes arguments that do not satisfy a tool's contract.
- **Domain failures:** the requested domain operation cannot be fulfilled under business rules.
- **Infrastructure failures:** an external system, model API, or communication channel fails.
- **Control failures:** execution reaches a limit, times out, or cannot continue safely.

These failures should not all be treated as interchangeable.

Pydantic AI provides mechanisms for communicating recoverable failures back to the model and for controlling retries. Other failures should propagate to the application or be converted into a deliberately defined application result.

Broad exception handling can hide programming defects and erase the reason an operation failed. Reliable design requires clear ownership of each failure and an explicit decision about whether to retry, ask for input, terminate, or escalate.

## 13. Usage limits, performance, and cost

An agent may make multiple model requests and tool calls during a single run. Consequently, the cost of an agent execution is not equivalent to the cost of a single model request.

Pydantic AI supports usage limits covering dimensions such as model requests, tool calls, tokens, and estimated monetary cost. These limits help bound execution but should not be treated as absolute billing guarantees or substitutes for provider-side spending controls.

A robust resource policy also considers timeouts, concurrency, external API quotas, tool-level work limits, and repeatability of side effects.

Performance should be evaluated across three dimensions: **quality of outcome, operational latency, and resource consumption**. Optimizing only token cost can undermine correctness, while optimizing only answer quality can make an application financially impractical.

## 14. Security and trust boundaries

Pydantic AI assists with typed tool integration and controlled execution, but it does **not** make an agent secure by default.

The principal boundaries are:

- **Instructions versus data:** retrieved content and tool results must not acquire instruction authority.
- **Model proposals versus application permissions:** a model's requested action is not an authorization decision.
- **User identity versus model arguments:** trusted user and tenant identity must be resolved by the application.
- **Structured data versus trusted facts:** validation verifies format and selected constraints, not truth.
- **Read-only tool design versus runtime policy:** tools must be genuinely read-only and scoped appropriately; a prompt cannot enforce this alone.

Major concerns include prompt injection, unauthorized data access, secret exposure, excessive tool permissions, uncontrolled spending, misleading model conclusions, and insufficient auditability.

Defenses belong at several levels: narrowly scoped tools, input validation, authorization, least privilege, sensitive-data handling, execution limits, and observability. No single prompt rule can replace these controls.

## 15. Observability and engineering confidence

An agent should be inspectable as a sequence of events, not judged only by its final answer. Useful observations include model requests, selected tools, argument validation outcomes, tool execution results, timing, errors, resource usage, and final output validation.

Tracing helps determine **what happened**. Evaluation helps determine **whether the behavior met its intended quality standard**. These are related but distinct concerns.

A well-formed response does not prove the agent followed an appropriate path. Conversely, a failed task may reveal a deficient tool contract or missing context rather than a weak model.

Testing and systematic evaluations are covered in separate training material. Their absence from this chapter is a matter of scope, not an assertion that they are optional in production.

## 16. Deliberate limits of this educational module

This repository teaches architecture and framework mechanics. It is **not** presented as a production-grade incident-response platform or a security-certified agent runtime.

The educational implementation is deliberately bounded. Its design does not claim comprehensive handling of production authorization, durable workflows, external-service outages, tenant isolation, strict budget enforcement, end-to-end auditing, or mature evaluation coverage.

These limitations are understood and intentionally separated from the core learning objective. They should not be copied into a production environment without further design, review, and hardening.

The absence of an `AGENTS.md` file in the repository is also deliberate. The training encourages developers to reason about the architecture and implement solutions independently rather than delegate the exercises to coding agents.

## 17. Key conclusions

Pydantic AI makes agent development more structured by bringing model interaction, tool registration, argument schemas, runtime control, and typed final outputs under one framework.

The most important lessons are conceptual:

1. **The model proposes; the application controls.**
2. **Tools are explicit capability boundaries, not unrestricted model powers.**
3. **A valid schema does not guarantee a valid conclusion.**
4. **Instructions guide behavior; authorization must be enforced in code.**
5. **Context, dependencies, and message history serve different purposes.**
6. **Framework-managed orchestration reduces boilerplate but not engineering accountability.**

The next learning stage examines **RunContext and dependency injection** in greater depth.

## Further reading

- [Pydantic AI — Agents](https://pydantic.dev/docs/ai/core-concepts/agent/)
- [Pydantic AI — Function Tools](https://pydantic.dev/docs/ai/tools-toolsets/tools/)
- [Pydantic AI — Dependencies](https://pydantic.dev/docs/ai/core-concepts/dependencies/)
- [Pydantic AI — Message History](https://pydantic.dev/docs/ai/core-concepts/message-history/)
- [Pydantic AI — OpenAI Models](https://pydantic.dev/docs/ai/models/openai/)
- [Pydantic AI — Model Settings](https://pydantic.dev/docs/ai/api/pydantic-ai/settings/)

---

*Vistware AI Agents Lab · Educational theory series · Module 02*

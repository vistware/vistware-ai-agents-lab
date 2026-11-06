# Module 04 — Conversation History, Context, and Persistence

**Vistware AI Agents Lab**  
**Technology:** Python 3.14 · Pydantic AI  
**Format:** Theory and architectural concepts  
**Audience:** Python developers and software architects

---

## 1. Purpose of this module

An AI agent can perform several model requests and tool calls during one execution without requiring an external memory mechanism. A different problem arises when a user expects a later execution to understand earlier questions, decisions, and findings.

This module explains how Pydantic AI carries conversation context across separate agent runs, what information is retained, and how that context can be stored outside a running Python process. It also addresses the boundaries between conversation history, application state, source data, and long-term memory.

The central engineering question is not **how much history can be stored**, but **which information must remain available for a subsequent operation to make sense**.

## 2. Run, conversation, and memory are different concepts

### Agent run

A **run** is a single invocation of an agent. It may include multiple model requests, function-tool executions, validation steps, and a final structured result. Pydantic AI manages the messages necessary for those steps within that run.

### Conversation

A **conversation** is a logical sequence of related runs. Later runs can inherit the context accumulated by earlier ones, allowing follow-up questions to refer to previous findings without repeating every detail in the new user prompt.

### Long-term memory

**Long-term memory** contains information intended to survive independently of any single conversation. Its selection, storage, retrieval, authorization, and retention policies form a separate architectural concern. Preserving a conversation is not equivalent to building a general long-term memory system.

## 3. When conversation history is useful

History is valuable when later requests depend on previous exchanges: a continuing investigation, iterative analysis, an evolving set of constraints, or a follow-up referring to earlier results.

History is usually unnecessary for an independent, one-shot task whose complete inputs are supplied on every invocation. Adding it by default can increase cost, couple otherwise independent operations, and complicate isolation.

Within a single run, tool results are already part of the agent's execution context. A separate conversation mechanism becomes relevant primarily when the task spans **multiple runs**.

## 4. Message history in Pydantic AI

Pydantic AI exposes the messages associated with an execution through the resulting run object.

- **`all_messages()`** provides the available history, including prior runs when such history was supplied.
- **`new_messages()`** provides the messages produced by the current run.
- **`message_history`** allows a later run to continue using previously collected messages.

These methods distinguish **the accumulated transcript** from **the portion newly produced by one execution**. This matters when a calling application collects messages incrementally: repeatedly appending the entire accumulated transcript would duplicate earlier content.

A message history can contain much more than user and assistant text. Tool calls, tool results, and provider-specific message parts may also contribute to the conversation. The history should therefore be treated as structured execution data rather than an ordinary string transcript.

## 5. The `Conversation` abstraction

Pydantic AI also provides a **`Conversation`** object, which represents a more complete continuation state than a list of messages.

In addition to the messages, a conversation can carry:

- Its conversation identifier.
- Accumulated usage information across related runs.
- State associated with pending deferred tool requests, when applicable.

A subsequent run receives this state through the **`conversation`** parameter. The resulting run exposes the updated conversation for further continuation.

**`message_history` and `conversation` are alternative ways to continue an agent.** They are not meant to be supplied together in the same run.

### Choosing between the two

Use **`message_history`** when the application intentionally works with message-level data: inspecting, selecting, transforming, or transferring a transcript. Use **`Conversation`** when the application wants to carry the fuller conversation state through successive executions.

Neither approach automatically makes the model more capable, expands its context window, or supplies facts absent from the available messages. With equivalent message content, the information presented to the model is broadly comparable; the important difference is the additional state carried by `Conversation`.

## 6. Usage accounting and limits

Token and request usage are separate from conversational meaning, but they matter operationally.

When an application continues a `Conversation`, accumulated usage is part of the continued state. Usage limits can therefore constrain the **conversation as a whole**, rather than only a single run. A limit reached after several runs is an expected safety mechanism, not necessarily a defect in the agent.

When only messages are supplied, accumulated usage from previous runs is not carried in the same way. Limits may then apply to each run independently unless the application enforces a separate cross-run budget.

A usage limit is an application safeguard, not an absolute guarantee of the final amount billed by a model provider. The application still needs to understand the provider's pricing, retries, and reporting behavior.

## 7. Persistence: saving and restoring a conversation

Conversation context held solely in process memory disappears when that process ends. **Persistence** makes continuation possible after an application restart or across separate application instances.

Pydantic AI provides **`ConversationTypeAdapter`** to serialize and validate a `Conversation`, including its richer state. Serialized conversation data can be stored in a JSON file or in an application-controlled persistence system.

A typical lifecycle has four conceptual stages:

1. Obtain an existing conversation or begin a new one.
2. Pass the conversation into an agent run.
3. Retrieve the updated conversation after the run.
4. Persist that updated state so it can be restored later.

Persistence is **not automatic** merely because `Conversation` is used. Choosing storage, handling read and write failures, and defining retention are responsibilities of the surrounding application.

For a small educational application, one local JSON file can be sufficient. A multi-user service requires stronger ownership rules, suitable storage, and concurrency handling. Writing each updated conversation to a single shared file would not preserve multiple independently resumable conversations.

## 8. Conversation isolation

**Conversation isolation** means that an unrelated run must not receive the transcript or state of another conversation by accident.

This does not imply that separate conversations require separate agent definitions, nor does it require different underlying data sources. The same agent and the same authorized data source can serve multiple independent conversations while maintaining distinct contextual histories.

Isolation has two dimensions:

- **Context isolation:** a newly initiated conversation does not inherit the prior conversation's messages or usage state.
- **Stored-state isolation:** the application can safely distinguish, retain, retrieve, and authorize different persisted conversations.

A single JSON file that is overwritten whenever a new conversation starts can demonstrate context isolation, but it cannot retain multiple independent histories for later retrieval. That is a deliberate limitation, not a contradiction.

A conversation identifier is useful for correlation and retrieval, but **an identifier is not an authorization check**. A production service must verify that the requesting user is permitted to access the stored conversation.

## 9. Context engineering and growing histories

Persisting more messages does not imply that every message deserves to be sent to the model forever. The available context window is finite, and the volume of input tokens can grow over successive runs.

A longer context can improve continuity, but may also increase latency, cost, and the chance that relevant information is obscured by unrelated material.

Common strategies include retaining the full history while it remains small, selecting recent or relevant portions, summarizing older segments, and compacting large tool outputs. Pydantic AI provides history-processing mechanisms for applications that need this control.

Such transformations require care. Tool calls and their results form structured relationships; indiscriminate truncation can remove information needed to interpret later messages. Summarization can also omit details or introduce inaccuracies. A compacted history should not silently become the authoritative record of source data.

**Context management and persistence solve different problems:** persistence keeps state available over time; context management controls what is supplied to the model for a particular request.

## 10. Conversation history is not the source of truth

A conversational answer can describe source records, but it is not a substitute for the records themselves.

In a data-analysis agent, the underlying dataset remains authoritative. Conversation history serves mainly to interpret references, constraints, and previous findings. If source data changes, an earlier answer may become stale even though it is preserved faithfully in the conversation.

Structured outputs help the calling application consume results predictably. They do not independently prove that model-generated conclusions or counts are factually correct. Reliable analysis still depends on validated source data, properly constrained tools, and careful treatment of uncertainty.

## 11. Validation and error boundaries

Data validation and conversation management should have distinct responsibilities.

Pydantic can validate structured records read from an external source. If a source record is invalid, an application may deliberately adopt a **fail-fast** policy: stop processing instead of silently skipping or fabricating data. Such a policy is a legitimate design choice for an educational module focused on context management.

Conversation deserialization is another validation boundary. The absence of a saved conversation and a damaged or incompatible saved representation are not the same condition, even if a simple demonstration chooses a similar fallback for both.

Advanced recovery policies, retries, backoff, schema migrations, and comprehensive exception handling are outside the scope of this module. Their absence in a learning project should be made explicit rather than mistaken for a production recommendation.

## 12. Security and privacy of stored conversations

A persisted conversation can include user prompts, tool results, operational details, and other sensitive information. Saving it to JSON does not make it harmless.

Important design obligations include:

- Restricting access to stored histories and enforcing conversation ownership.
- Avoiding the storage or disclosure of credentials and other secrets.
- Defining retention and deletion policies appropriate to the data.
- Treating untrusted message histories and tool outputs as data, not instructions with elevated authority.
- Avoiding accidental disclosure through logs, debugging output, repository commits, or shared storage.

A history submitted by an untrusted client must not automatically be treated as trusted server-side state. Prompt instructions alone are not a security boundary; actual permissions must be enforced by application code and infrastructure.

## 13. Architectural decisions and trade-offs

A well-designed agent does not need the most elaborate memory system available. The appropriate solution follows the actual workflow.

For a single self-contained execution, use the run's built-in context. For a simple multi-turn workflow, message history may be enough. For continuity that includes usage and deferred state, `Conversation` is a stronger fit. For continuation after restart, add explicit persistence. For a multi-user service, add conversation ownership, access controls, storage concurrency, and lifecycle management.

These are separate decisions. They should not be bundled into one abstraction before the application genuinely needs them.

## 14. Deliberate scope of Module 04

This module teaches the behavior and architectural meaning of conversation state. Its educational implementation may intentionally use a local dataset, a single process, one JSON persistence file, and controlled command-line execution.

The module does **not** claim to provide production-grade multi-tenant storage, long-term semantic memory, fully automated recovery, exhaustive testing, or optimized context compaction. Those are distinct engineering topics that can be introduced after the underlying conversation mechanisms are understood.

## 15. Core takeaways

- An agent run already maintains the context needed for its internal tool loop.
- Cross-run continuity requires passing prior context explicitly.
- `message_history` transports messages; `Conversation` transports a fuller continuation state.
- `Conversation` can retain accumulated usage, which changes how limits behave across runs.
- `ConversationTypeAdapter` enables serialization and restoration, but persistence remains an application responsibility.
- A new conversation must not accidentally inherit another conversation's history.
- Persisted history does not replace authoritative source data, security controls, or context management.
- Memory is useful when the workflow requires continuity; otherwise, it is unnecessary complexity.

## Further reading

- [Pydantic AI — Messages and Chat History](https://pydantic.dev/docs/ai/core-concepts/message-history/)
- [Pydantic AI — Persistence](https://pydantic.dev/docs/ai/core-concepts/persistence/)
- [Pydantic AI — Agents and Usage Limits](https://pydantic.dev/docs/ai/core-concepts/agent/)

---

*Vistware AI Agents Lab — educational engineering notes. The accompanying source code is a learning demonstration, not a production-ready incident-management platform.*

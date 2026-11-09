# Module 06 — Context Optimization in Pydantic AI

**Vistware AI Agents Lab | AI Agents Engineering | Theory**

> This module explains how to manage conversation context deliberately, why shorter histories are not necessarily cheaper, and how Pydantic AI supports compaction and measurement. It is educational documentation rather than a production configuration guide.

## 1. Learning objective

An agent can work correctly with a short conversation yet gradually become slower, more expensive, or less reliable as previous messages accumulate. Context optimization is the engineering discipline of controlling the information sent to the model **without losing what is required to answer the current request correctly**.

The objective is not to minimize tokens in isolation. It is to preserve task quality while managing context limits, latency, model requests, cache behavior, and cost.

This module builds on earlier topics: agent loops, structured tool outputs, `RunContext`, conversation history, and error handling.

## 2. What occupies the context window?

A model request can include several distinct kinds of information:

- **Agent instructions:** the current operating rules, task boundaries, and expected behavior.
- **Conversation messages:** earlier user requests and model responses.
- **Tool calls and tool results:** the data gathered during earlier reasoning steps.
- **The current request:** the user's latest question and associated inputs.
- **Schemas and other provider-visible material:** tool definitions, structured-output specifications, and supported additional content.

The context window is finite. A conversation can contain many messages while still fitting comfortably, or only a few messages containing very large tool responses that consume most of the window.

**Message count is not token count.** These metrics describe different aspects of a conversation and should not be substituted for each other.

## 3. Conversation state versus model context

A persisted conversation represents the available state of an ongoing interaction. The **effective model context** is the information actually supplied to the model for a particular request.

These concepts overlap but are not identical. Context processing can shorten or transform history before the next request. Pydantic AI's compaction mechanisms can also modify the history retained by the running conversation, meaning that the change persists into later steps rather than disappearing after a single request.

A compacted conversation is therefore not guaranteed to retain its earlier messages verbatim. Information removed by destructive compaction cannot be reconstructed from the compacted history alone.

This distinction matters when conversation state is also serialized or restored between program executions.

## 4. Why large histories are challenging

Long histories create several potential problems:

1. **Context-window pressure.** Requests can eventually exceed the model's supported capacity.
2. **Additional input processing.** Repeated historical content is included in subsequent requests.
3. **Longer latency.** Processing more content can increase end-to-end response time, depending on the provider and model.
4. **Retrieval difficulty.** Important facts can be buried among irrelevant material.
5. **Increased sensitivity to stale information.** Earlier tool results can remain in the conversation even after the underlying data changes.
6. **Cost variability.** Provider pricing, cached input tokens, generated output, and the number of model requests all affect the final charge.

Consequently, a larger context can be valuable, unnecessary, or actively counterproductive depending on the task.

## 5. Main context-management strategies

| Strategy | Behavior | Principal trade-off |
|---|---|---|
| Full history | Retains all available messages | Maximum detail, growing context |
| Sliding window | Removes older messages and retains a recent tail | Low processing overhead, loss of old facts |
| Selective history | Keeps messages judged relevant | Selection itself may omit essential evidence |
| Summarization | Replaces older content with a condensed account | Extra model work and possible summary errors |
| Tool-result reduction | Clears, deduplicates, or limits historical tool data | Smaller history but less original evidence |
| Tiered compaction | Uses cheaper reductions before more expensive ones | More policy complexity, potentially better efficiency |

No strategy is universally superior. Each is a policy about the importance of older information.

## 6. SlidingWindowCompaction

`SlidingWindowCompaction`, provided by the Pydantic AI Harness compaction facilities, is a **zero-LLM** approach. It reduces context by discarding older whole messages and keeping a recent tail after a configured threshold is exceeded.

Its key concepts include:

- **Trigger threshold:** when a conversation becomes large enough for compaction to run. A threshold can be based on message count or estimated token usage.
- **Retention budget:** how much of the recent history remains after compaction.
- **Preserving the initial user request:** the strategy can keep the first user message even when it would otherwise fall outside the retained tail.
- **Tool integrity:** the strategy preserves necessary relationships between tool calls and tool results rather than leaving invalid orphaned pairs.

Sliding windows are attractive when recency is a reliable proxy for relevance. They are less suitable when an old instruction, earlier decision, identifier, or constraint continues to matter.

Keeping the first user message helps retain the initial task, but **does not guarantee preservation of all intermediate findings**.

## 7. SummarizingCompaction

`SummarizingCompaction` uses an additional model request to condense older messages into a shorter representation, while preserving a recent portion of the conversation.

Compared with a sliding window, it may retain more of the *meaning* of earlier work. However, it introduces new risks and costs:

- The summary consumes model requests and tokens.
- It can omit details that become important later.
- It can distort uncertainty, chronology, identifiers, or constraints.
- Repeated summarization can gradually degrade information unless carefully managed.
- The condensed history is not a lossless replacement for the original messages.

Incremental summarization can update an earlier summary instead of repeatedly producing a new summary from scratch. This reduces some duplication but does not eliminate information-loss risk.

Summarization is most useful when older facts remain relevant and the savings across future requests justify the cost of generating the summary.

## 8. Other compaction approaches

The broader Pydantic AI Harness compaction toolkit includes approaches aimed at specific sources of context growth:

- **ClearToolResults:** reduces older tool-result content while preserving the structural relationship with the tool calls.
- **DeduplicateFileReads:** avoids retaining redundant file-read content where newer equivalent reads supersede it.
- **ClampOversizedMessages:** reduces individual oversized message parts rather than waiting for an entire conversation to grow too large.
- **TieredCompaction:** progressively applies strategies, typically trying less expensive reductions before model-based summarization.
- **ReportContextUsage:** reports context usage but does not itself compact history.

The right intervention depends on whether the context is dominated by repeated tool results, stale conversation turns, a single oversized response, or genuinely useful older material.

## 9. ProcessHistory and capabilities

Pydantic AI uses a capability-based extension system for processing request history. `ProcessHistory` is one mechanism for transforming the messages available to the next model request. Harness compaction strategies offer prebuilt policies for common cases.

This creates a distinction between:

- **History processing:** applying an application-defined transformation to messages.
- **Compaction policy:** deciding when and how information should be removed or summarized.
- **Observability:** reporting what happened without necessarily changing the history.

History modification should preserve valid message structure. Deleting an arbitrary message without considering associated tool calls and returns can produce inconsistent request histories.

The Pydantic AI Harness compaction API is version-sensitive; verify its current documentation and the installed package version before using a particular option in an application.

## 10. Prompt caching is not context reduction

Prompt caching and context compaction address different problems.

**Context reduction** sends fewer or smaller pieces of information to the model.

**Prompt caching** may allow a model provider to reuse a previously processed, matching prefix of a request. Cached input tokens still belong to the request's input usage, but providers may charge a lower rate for eligible cached tokens.

As a result, a full, stable history can sometimes be cheaper than a shorter but frequently rewritten history. Compaction changes message content or ordering and may invalidate a reusable cache prefix from the changed point onward.

A reduction in token count **does not guarantee a reduction in billed cost**. Conversely, high cache reuse does not mean the effective context has become smaller.

Cache behavior depends on provider, model, request similarity, eligibility, and time between requests. It must be measured rather than assumed.

## 11. Reading usage metrics correctly

Several metrics are useful but answer different questions:

| Metric | What it measures |
|---|---|
| Model requests | Number of model requests counted by the agent runtime |
| Tool calls | Number of tool invocations represented in usage |
| Input tokens | Input-token consumption across model requests |
| Output tokens | Generated-token consumption |
| Reasoning tokens | Provider-reported reasoning-token usage, when available |
| Cached input tokens | Input tokens served from provider cache, when reported |
| Estimated cost | Monetary estimate derived from provider usage and pricing information |
| Retained messages | Number of messages remaining in the conversation history |
| Context-window utilization | The estimated share of a model's context window used by a request |

**Cumulative versus per-run accounting matters.** A continued `Conversation` can carry usage from previous runs, so a displayed total may describe the entire conversation rather than only the latest question. For a clean comparison, distinguish cumulative counters from the incremental usage of each run.

Furthermore, cumulative input tokens across several requests are not the same as the number of tokens sent in a single request. Message count is not sufficient to infer either value.

## 12. Measuring optimization fairly

Reliable comparisons require control of the variables that can influence the result:

- Use the same source data and the same sequence of user requests.
- Keep the model, reasoning configuration, tools, and output schema consistent.
- Start from independent conversation states for different strategies.
- Account for different numbers of model requests and tool calls.
- Measure both input and output tokens, cache reuse, and cost.
- Check whether the final answer remains correct and sufficiently grounded.
- Avoid interpreting a single run as a universal performance result.

LLM-driven tool selection can vary between executions. Differences in model behavior, cache availability, or request count can alter costs even without changes in compaction policy.

An optimization should therefore be evaluated against a **quality requirement**, not merely against the smallest token total.

## 13. What the Vistware lab demonstrated

The module explored the interaction between full conversation history and sliding-window compaction. A shorter retained history produced substantially lower reported token usage in the observed runs, while the full-history variant benefited from stronger cache reuse and a lower estimated cost in that comparison.

That observation supports a broader principle, **not a universal ranking**: reducing context can reduce token consumption while worsening cost efficiency if it disrupts caching or changes the agent's request pattern.

The educational implementation deliberately retains full history by default and keeps sliding-window compaction available as a configurable experimental option. This is a decision tied to the observed scope and workload, not a claim that full history is always the best production strategy.

## 14. Preserve meaning, not just messages

Conversation history is useful because it preserves references, decisions, constraints, and evidence across turns. Losing these relationships can make later requests ambiguous.

High-value information may include:

- The user's current objective and filters.
- Explicit constraints or corrections supplied earlier.
- Important identifiers and decisions.
- Whether a previous finding was confirmed or provisional.
- Whether underlying source data may now be stale.

A compacted summary that retains only fluent prose but omits such details can degrade subsequent reasoning.

For changing business data, the underlying data source remains authoritative. A stored historical answer should not silently be treated as a fresh read.

## 15. Security and lifecycle considerations

Conversation histories may contain user-provided information, external tool outputs, and sensitive operational details. Optimization and persistence must respect the application's boundaries of trust and access.

Conceptually:

- Treat tool results as data, not as instructions with elevated authority.
- Avoid letting context transformations turn untrusted content into trusted commands.
- Keep separate conversations isolated from one another.
- Apply appropriate retention and deletion policies to persisted state.
- Recognize that compaction can remove information needed for later auditing or debugging.

These are architectural considerations; simply enabling a compaction strategy does not implement security or access control.

## 16. Choosing a strategy

**Prefer full history** when conversations are short, earlier details matter, and the observed costs remain acceptable.

**Consider a sliding window** when the interaction is mostly local to recent turns and older content can safely be discarded.

**Consider summarization** when older context remains important but must be represented more compactly, and the additional model cost is justified.

**Consider tool-result reduction** when large tool responses dominate the history and can be retrieved again from their authoritative source.

**Consider tiered approaches** when simple reductions are insufficient and the conversation workload justifies a more complex policy.

The strategy should follow the workload, not the other way around.

## 17. Key takeaways

1. Context engineering is about preserving useful information within a finite budget.
2. A conversation's stored history and the context of an individual model request are related but distinct.
3. Sliding windows save context by discarding information; summarization saves context by compressing it imperfectly.
4. Pydantic AI's compaction facilities preserve tool-call/tool-result structure and can modify the retained history.
5. Prompt caching can reverse the expected cost advantage of shorter prompts.
6. Usage metrics must distinguish cumulative conversation totals from individual-run consumption.
7. The target of optimization is **reliable, correctly grounded output at an acceptable cost and latency**.

## Official documentation

- [Pydantic AI Harness — Compaction](https://pydantic.dev/docs/ai/harness/compaction/)
- [Pydantic AI — Process History](https://pydantic.dev/docs/ai/capabilities/process-history/)
- [Pydantic AI — Messages and Chat History](https://pydantic.dev/docs/ai/core-concepts/message-history/)
- [OpenAI API — Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)
- [OpenAI API — Pricing](https://platform.openai.com/pricing)

---

*Vistware AI Agents Lab — Learn the mechanisms, understand the trade-offs, and make evidence-based engineering decisions.*

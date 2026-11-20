# Module 07 — Retrieval-Augmented Generation (RAG)

**Vistware AI Agents Engineering · Educational reference**

> **Educational project — not production-ready software.** This module is a hands-on exploration of the principles behind retrieval-augmented generation. It uses synthetic incident reports and operational runbooks, a local JSON-based knowledge index, and a Pydantic AI agent. It is intended for learning and architectural discussion, not for handling real incidents, confidential documents, or business-critical decisions without additional engineering and validation.

## Overview

A language model can reason about information presented in its context, but it does not automatically know an organization's current internal documentation. Retrieval-augmented generation (RAG) addresses that gap by finding relevant external information and supplying it to the model when an answer is generated.

Module 07 explores this pattern through a fictional incident-investigation assistant. The assistant answers questions about microservices, authentication, payments, deployment failures, and operational procedures using a small collection of Markdown knowledge documents. The emphasis is on understanding **how knowledge becomes searchable, how search results reach an agent, and what it means to ground an answer in evidence**.

This module extends earlier work on Pydantic AI agents, tool calling, dependency injection, conversation history, error handling, and context management. Unlike conversational memory, which represents earlier interactions, retrieval brings relevant information from an independent knowledge source into the current execution.

### At a glance

| Layer | Responsibility | Approach in this module |
| --- | --- | --- |
| Knowledge source | Provide reference material | Fictional Markdown runbooks and incident reports |
| Ingestion | Read, identify, and validate source documents | File scanning, Pydantic models, content hashes |
| Chunking | Divide documents into retrievable units | Markdown header boundaries, followed by length-based splitting |
| Embeddings | Represent chunks and questions as vectors | Pydantic AI `Embedder` with OpenAI embeddings |
| Persistence | Retain prepared knowledge between runs | Local JSON files, including index metadata |
| Retrieval | Rank chunks against a question | Exact vector comparisons with NumPy, followed by Top-K |
| Agent | Ask for evidence and compose an answer | Pydantic AI tool calling and dependency injection |
| Grounding | Relate answers to retrieved sources | Structured output and run-scoped citation validation |

## 1. The RAG mental model

RAG is an architectural pattern, not a distinct type of language model. It separates three concerns:

1. **Retrieval:** Identify potentially relevant passages in an external knowledge source.
2. **Augmentation:** Add those passages to the context available to the language model.
3. **Generation:** Produce an answer while accounting for the supplied evidence and its limitations.

The complete flow has two sides:

**Preparation:** Markdown documents → structured sections → chunks → embedding vectors → persisted index.

**Question answering:** User question → query embedding → similarity ranking → retrieved passages → Pydantic AI agent → source-aware answer.

Preparation and question answering are deliberately separate. Rebuilding document embeddings for every question would waste time and API usage. Instead, document vectors are generated and stored ahead of time, while a query vector is generated when a new question arrives.

Retrieval does not establish truth on its own. It produces **candidate evidence**, and the agent must still determine what those passages actually support.

## 2. Documents, identity, and provenance

The knowledge base consists of fictional Markdown documents. A document may describe an incident's symptoms, confirmed root cause, unverified hypotheses, diagnostic procedure, recovery steps, and related procedures.

Reliable retrieval starts before any vector computation. Each source must remain identifiable so that a passage can be traced back to its original document. The ingestion layer therefore preserves source-related information alongside text. It uses source paths relative to the knowledge directory and hashes source bytes to detect content changes.

A content hash helps answer **“Has this source changed?”** It is not the same as an embedding, which addresses **“Which texts may be semantically related?”** These values serve different purposes and should not be confused.

Pydantic models make the prepared data explicit. Structured records capture document identity, content, section metadata, and later the corresponding embedding. Validation helps maintain a consistent index format, but it cannot guarantee that a fictional runbook is factually correct or that a diagnostic recommendation is safe.

### Document identity versus chunk identity

A single Markdown document can generate several retrievable chunks. The document's identity tells us *where the information came from*; a chunk's identity tells us *which passage was retrieved*.

In this module, chunk identifiers derive from the source identifier and the chunk's position in the generated sequence. This is deterministic for unchanged sources and unchanged chunking rules. It does **not** imply that identifiers are immutable after edits: inserting or splitting an earlier section may shift later chunk positions.

For production systems, stable identifiers, document versions, and provenance policies require explicit design decisions. The educational approach keeps these relationships visible without introducing a separate document-management platform.

## 3. Structure-aware Markdown chunking

Embedding an entire long runbook as one vector may blur together several unrelated concepts. Chunking creates smaller, more focused units that can be ranked independently.

This module starts with the structure already present in Markdown:

- The main title identifies the document's subject.
- Section and subsection headings provide topical context.
- Paragraphs under those headings provide the information to be retrieved.

A Markdown header splitter first identifies structured sections and retains header metadata. A second, character-based splitter can divide sections that exceed the configured length. The current implementation uses a maximum chunk size of **1,200 characters** with no overlap; this is a character limit, not a token limit.

The central trade-off is **semantic completeness versus retrieval granularity**. Very large chunks can contain several topics and consume unnecessary context. Very small chunks may lose the qualifiers needed to interpret a statement. For example, “restart the service” is not a useful standalone instruction if the affected service and prerequisites are missing.

Header metadata helps preserve context even when the text is split. Still, document structure is an imperfect proxy for semantic boundaries. Markdown heading-aware splitting is a pragmatic fit for this synthetic technical corpus; it is not a universal chunking strategy for contracts, scanned PDFs, or loosely structured prose.

Other strategies include fixed-size splitting, overlapping windows, paragraph-aware splitting, semantic segmentation based on embeddings, and LLM-assisted segmentation. More sophisticated splitting should be adopted because evaluations show a benefit, not simply because another model can be added to the pipeline.

## 4. Embeddings: a numerical representation of text

An embedding model converts text into a vector: an ordered sequence of real numbers. A vector can be thought of as a point or direction in a multidimensional space.

In two dimensions, a vector has two coordinates; in five dimensions, it has five. A text embedding has many more. For example, OpenAI's `text-embedding-3-small` uses **1,536 dimensions by default**. The individual coordinates do not have simple public labels such as “JWT,” “database,” or “authentication.” Relevant features are distributed across the representation.

Embedding models are trained so that text with related meanings often has a similar geometric representation. A question about being unable to sign in can therefore be close to a passage describing authentication failure, even if their wording differs.

This is an opportunity, not a guarantee. Embeddings can conflate related but different events, struggle with precise identifiers, or rank a rejected hypothesis above the confirmed cause of an incident.

### Document embeddings and query embeddings

Pydantic AI's `Embedder` exposes separate operations for preparing documents and for representing queries. This distinction matters because some embedding architectures treat those two tasks differently.

In this module, the same configured embedding model supports both operations. A searchable index must not silently mix vectors from incompatible models or configurations. The persisted index records the model identity and vector dimensionality, and retrieval checks compatibility before comparing vectors.

More dimensions do not automatically mean more accurate retrieval. Quality depends on training data, model objectives, language, domain, chunking, and the questions being asked. A larger representation also has storage and computation costs.

## 5. Semantic search and cosine similarity

Traditional lexical search emphasizes terms, their frequency, and exact matches. Semantic search compares vector representations. Both approaches are useful, but they answer different needs.

**Cosine similarity** measures the angle between two nonzero vectors:

\[
\operatorname{similarity}(\mathbf{a},\mathbf{b})=
\frac{\mathbf{a}\cdot\mathbf{b}}{\|\mathbf{a}\|\,\|\mathbf{b}\|}
\]

Its theoretical range is −1 to 1. A value of 1 means the vectors point in the same direction; 0 means they are orthogonal; −1 means they point in opposite directions.

The numerical score is **not a calibrated probability**. A similarity of 0.90 does not mean a passage has a 90% chance of containing a correct answer. It describes a geometric relationship between representations produced by an embedding model.

OpenAI embeddings are normalized to unit length. For such vectors, their dot product equals cosine similarity. The module uses NumPy to compute these comparisons directly, without a vector database or an approximate nearest-neighbor index.

### Ranking and Top-K

For each question, the retriever obtains the query vector, compares it with all indexed chunk vectors, sorts the resulting scores in descending order, and returns the highest-ranked passages.

**Top-K** limits the number of returned candidates. This module uses **three results by default** and accepts a range of **one to five**. Increasing K can reveal complementary evidence from different documents, but it also introduces more irrelevant material and additional context cost.

A critical limitation: Top-K returns the *best available matches*, not necessarily *good matches*. If the index only contains operational incidents and a user asks about company revenue, the highest-ranked incident passages still may have nothing to do with the answer. A relatively high similarity score also does not establish factual support.

There is no universally correct similarity threshold. A useful cutoff depends on the embedding model, document corpus, query distribution, and evaluation criteria. This educational implementation focuses on explicit ranking and leaves sophisticated relevance calibration and reranking outside its scope.

### Why no vector database?

A linear scan is easy to inspect and adequate for a small collection of passages. Its vector comparison cost grows approximately with the number of chunks multiplied by the embedding dimension. The module also sorts the candidate results.

At larger scales, products such as PostgreSQL with pgvector or specialized vector engines can provide indexing, metadata filtering, and approximate nearest-neighbor search. Those technologies would replace parts of the storage and retrieval implementation, not the underlying ideas of embedding generation, ranking, evidence selection, or grounded answering.

For exact codes, filenames, and identifiers, lexical search can be a better fit than semantic search. A production knowledge system may therefore combine both approaches in **hybrid retrieval**, sometimes with a separate reranking stage.

## 6. Persistence, synchronization, and freshness

Prepared knowledge is stored locally in two logical forms:

- **Parsed knowledge:** source information, content hashes, chunk content, and section metadata.
- **Embedded knowledge:** chunk content and metadata together with vectors, embedding model identity, and dimensionality.

The ingestion step rebuilds the set of parsed files from currently available source documents. As a result, a document removed from the scanned directory no longer belongs to the next parsed state. Embedding synchronization subsequently constructs the index from that parsed state, removing chunks no longer present.

When an unchanged chunk can be matched to a previous index entry, its embedding can be reused. Changed content requires a new vector. A forced rebuild is available when all vectors must be regenerated. Index metadata prevents accidental reuse under a different configured embedding model.

JSON is intentionally chosen for transparency: its structure can be inspected without specialized tooling. It is not an efficient general-purpose vector store. Large vectors create substantial text files, and loading or scanning them becomes increasingly expensive as the corpus grows.

The module writes prepared data via temporary files and replacement, reducing the chance of leaving a partially written JSON file. This is useful but is not equivalent to a transactional database, distributed synchronization, or complete recovery from concurrent modifications.

**Freshness is a workflow property.** Updating a Markdown file does not automatically update an existing query result. The source must be parsed and the embedding index synchronized before the agent can search the new knowledge. A document's presence in conversation history is likewise not proof that the source remains current.

## 7. Pydantic AI integration and dependency injection

The incident-investigation agent uses Pydantic AI for model interaction, tool calling, typed dependencies, and structured outputs.

The retrieval algorithm remains a separate application component. The agent is given a **search tool** that delegates to the retriever; it does not implement similarity search inside the tool or expose raw embedding vectors to the language model.

The tool accepts a query and a bounded number of results. It returns evidence records containing the original passage, source identity, section metadata, a chunk identifier, and a similarity score. These details allow the model to reason about the retrieved text and provide source references.

A typed dependency object supplies the retriever through `RunContext`. This preserves an important trust boundary:

- The **model** may formulate a search query and request a permitted result count.
- The **application** controls the retriever instance, the available index, validation, and permitted argument range.

Instructions ask the agent to search before answering, including for questions outside the knowledge base. Instructions alone do not guarantee tool use, however. The module additionally checks for a successful search-tool return in the current run before accepting the final output.

This illustrates a general principle of agent engineering: **behavior requested in a prompt is not the same as a rule enforced in application code**.

## 8. Grounding, uncertainty, and source validation

**Grounding** means relating an answer to the evidence made available for that answer. It is different from retrieval. Retrieval proposes passages; grounding requires that conclusions remain within what those passages justify.

For incident analysis, this distinction matters especially when documentation contains both confirmed findings and unverified hypotheses. A hypothesis about Kafka replay, for example, must not be presented as an established cause merely because it appeared among the retrieved passages.

The agent's structured response separates:

| Field | Meaning |
| --- | --- |
| Answer | Human-readable explanation and relevant qualifications |
| Knowledge status | Whether the retrieved documentation sufficiently supports the answer |
| Chunk identifiers | The specific retrieved passages cited by the answer |

A response can indicate **supported** or **insufficient** knowledge. When evidence is missing or incomplete, the intended behavior is to explain the limitation rather than manufacture a diagnosis or company fact.

### Why citation validation lives in Python

A language model can invent a plausible-looking citation identifier. Merely asking it to cite sources does not prove that those sources were actually retrieved.

The module addresses this by tracking the identifiers returned from successful knowledge-search calls. Those identifiers are carried as tool-return metadata and checked against the citations in the structured answer. The validator scopes the evidence to the **current agent run**, avoiding accidental acceptance of identifiers from unrelated executions. If the answer cites an unknown chunk, or claims to be supported while citing none, the model receives a retry request.

This is a stronger guarantee than prompt-only citation instructions, but its scope is precise:

**A valid citation proves that the passage was retrieved, not that the passage supports every claim made about it.**

Semantic faithfulness, factual correctness, completeness, and the safety of an operational recommendation still require separate assessment. In this learning module, those aspects are explored through inspection of answers and their retrieved evidence rather than a full automated evaluation framework.

### Retrieved text is untrusted data

A document might contain words that look like agent instructions. Such text remains source content, not a trusted system directive. The model is instructed to ignore attempts by retrieved documents to change its role, bypass its rules, or manipulate citations.

This separation is necessary but not a complete prompt-injection defense. In production systems, sensitive data access and authorization must be enforced by the application before any retrieved content reaches the model.

## 9. What the demonstration shows

The module's entry points support four distinct activities: preparing Markdown knowledge, synchronizing embeddings, inspecting semantic search independently, and running the incident-investigation agent with sample questions.

The examples deliberately include related technical topics with different causal explanations. This makes ranking errors visible: a passage can mention the same service, technology, or symptom while describing an unrelated incident or an explicitly rejected hypothesis.

They also include questions outside the corpus. When asked for a company's revenue rather than an operational incident, a well-behaved agent should acknowledge insufficient evidence rather than infer a financial figure from payment-related runbooks.

These observations are educational demonstrations, **not a measured accuracy benchmark**. Individual examples cannot establish recall, precision, factuality, reliability, or generalization across a broader enterprise corpus.

## 10. Architectural decisions and trade-offs

| Decision | Benefit | Limitation |
| --- | --- | --- |
| Markdown as the knowledge source | Human-readable, structured, easy to inspect | Depends on document quality and heading conventions |
| Header-aware chunking | Preserves topical sections and metadata | Structural boundaries do not always match semantic ones |
| Secondary length-based splitting | Controls oversized sections | Character limits do not equal token limits |
| Local JSON storage | Transparent and simple for experimentation | Large files, full scans, limited concurrency |
| Exact cosine ranking | Easy to reason about and debug | Linear scan cost grows with corpus size |
| Bounded Top-K | Limits material passed to the model | May omit evidence or return irrelevant candidates |
| Pydantic AI tool with typed dependencies | Clear application/model boundary | The model's choice of query can still be imperfect |
| Structured source validation | Rejects citations not returned in the current run | Does not verify semantic entailment of each claim |

The broader engineering lesson is to **use existing components when they solve the right problem**. Writing a custom vector database, an embedding model, or a new agent framework is unnecessary for this educational goal. The valuable architectural work lies in controlling data flow, validating boundaries, making uncertainty visible, and selecting technologies based on measured needs.

## 11. Limitations and production considerations

**This repository is an educational reference, not a production RAG service.** It deliberately omits or simplifies capabilities that a real deployment may need:

- **Access control and tenancy:** No end-to-end per-user document authorization or multi-tenant isolation policy.
- **Search quality:** No hybrid lexical/vector retrieval, learned reranking, or calibrated relevance threshold.
- **Evaluation:** No comprehensive golden dataset, automated retrieval evaluation, or factual-grounding benchmark.
- **Storage and scaling:** No production vector database, distributed indexing, high-concurrency ingestion, or service-level performance objectives.
- **Operational resilience:** No complete monitoring, alerting, rollback strategy, or disaster-recovery process for the knowledge index.
- **Security:** No complete defense against hostile documents, sensitive-data leakage, or adversarial prompt injection.
- **Source governance:** No full lifecycle for retention, revision history, approvals, audit trails, or deletion across distributed copies.
- **Answer guarantees:** Citation membership validation does not establish that a generated diagnosis is correct or safe to execute.

The code provides a controlled place to understand those missing concerns before deciding which ones are actually necessary for a particular application.

The synthetic runbooks must not be interpreted as real incident reports, operational instructions for live systems, or authoritative security guidance. Any production adaptation would require a threat model, access controls, representative evaluation data, observability, operational safeguards, and verification against real business requirements.

## 12. Key concepts to remember

**Embedding:** A learned numerical representation of text used for similarity comparisons.

**Chunk:** A retrievable fragment of a larger document, ideally with enough context to remain meaningful.

**Cosine similarity:** A geometric comparison of vector directions, not a probability of truth.

**Top-K:** A request for the highest-ranked candidates, not a guarantee of relevance.

**Vector index:** A storage and search arrangement for embeddings and their associated records.

**Retrieval:** Finding possible evidence relevant to a question.

**Grounding:** Constraining conclusions to information that the retrieved evidence can justify.

**Provenance:** The relationship between a passage and its original source.

**Citation validation:** Checking that cited identifiers correspond to retrieved passages; distinct from checking whether those passages prove the claims.

**Knowledge freshness:** The property that the searchable index reflects the intended version of its source documents.

---

### Closing perspective

Module 07 demonstrates a foundational RAG architecture with explicit boundaries: deterministic document preparation, reusable embeddings, numerical retrieval, agentic tool use, and verifiable source identities.

The goal is not to present a ready-made enterprise search platform. It is to make the inner workings of retrieval-augmented agents understandable enough that future choices—such as pgvector versus Qdrant, semantic versus hybrid search, or simple retrieval versus multi-step reasoning—can be made deliberately and evaluated with evidence.

*Part of the public Vistware AI Agents Engineering learning repository.*

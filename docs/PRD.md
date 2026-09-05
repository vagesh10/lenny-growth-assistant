# Product Requirements Document (PRD)

# The Lenny Growth Assistant

**Version:** 1.0
**Status:** Draft
**Product Type:** AI-powered knowledge assistant
**Primary Users:** Product Managers and Growth Leaders

---

## 1. Product Overview

The Lenny Growth Assistant is a full-stack AI-powered conversational application that allows Product Managers and Growth Leaders to ask product and growth questions using Lenny's Podcast transcripts as the primary knowledge source.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant transcript content before generating an answer. Responses must be grounded in the retrieved transcript content and should identify the relevant episode, guest, timestamp, or topic.

The application also provides two additional capabilities:

1. Generate approximately 1,250-word Ship 30 for 30-style essays from grounded knowledge.
2. Generate Markdown or HTML/CSS artifacts and render them directly inside the application.

The application supports both a local LLM through Ollama and a cloud LLM provider, allowing the evaluator to switch models without changing application code.

---

# 2. Problem Statement

Product Managers and Growth Leaders consume a large amount of information from podcasts, interviews, and industry discussions.

Lenny's Podcast contains valuable product-management and growth knowledge, but finding a specific insight can require manually searching through transcripts or listening to long episodes.

The user needs a faster way to:

* Find relevant product and growth insights.
* Ask questions in natural language.
* Receive answers grounded in the original podcast content.
* Identify the source behind each answer.
* Turn useful insights into reusable written content.
* Generate simple artifacts without leaving the application.

The core problem is therefore:

> **How can we turn a large collection of Lenny's Podcast transcripts into a reliable, searchable, conversational knowledge assistant for product and growth teams?**

---

# 3. Target User

## Primary Persona: Growth/Product Manager

The primary user is a Product Manager or Growth Leader who needs actionable product and growth knowledge quickly.

### User Goals

The user wants to:

* Ask product and growth questions naturally.
* Discover relevant ideas from experienced practitioners.
* Understand where an answer came from.
* Ask follow-up questions within the same conversation.
* Convert useful insights into an actionable article.
* Generate a small Markdown or HTML artifact when needed.

### User Pain Points

* Large volume of podcast content.
* Time required to search or listen to episodes.
* Difficulty connecting insights across different episodes.
* Lack of confidence in AI-generated answers when sources are unclear.
* Repeating the same research manually.

The assignment specifically frames the persona as a Growth PM who wants actionable tactics without manually going through 200+ hours of audio.

---

# 4. Product Goals

## Primary Goals

### Goal 1 — Grounded Question Answering

Allow users to ask product and growth questions and receive answers based strictly on relevant Lenny's Podcast transcript content.

### Goal 2 — Source Attribution

Every grounded answer should identify the relevant transcript source, such as:

```text
[Episode: Guest Name, Timestamp/Topic]
```

### Goal 3 — Content Generation

Allow users to transform grounded insights into an approximately 1,250-word Ship 30 for 30-style essay.

### Goal 4 — Artifact Generation

Allow users to generate Markdown or HTML/CSS artifacts and preview them inside the application.

### Goal 5 — Flexible Model Configuration

Allow the application to run using:

* Ollama/local LLM.
* Cloud LLM.

The model provider should be configurable without modifying the core application code.

### Goal 6 — Operational Readiness

Provide a reproducible local deployment using Docker Compose with documentation, logging, health checks, error handling, and automated tests.

---

# 5. Non-Goals

The following features are intentionally outside the scope of this assignment:

* User authentication and authorization.
* Payment processing.
* Multi-tenant enterprise accounts.
* Native mobile applications.
* Voice input/output.
* Fine-tuning a custom LLM.
* Training a new embedding model.
* Building a custom vector database.
* Complex analytics dashboards.
* Kubernetes-based production infrastructure.

These features do not directly contribute to the required evaluation criteria and would increase implementation complexity unnecessarily.

---

# 6. Core User Flows

## 6.1 New Chat

```text
User opens application
        ↓
Creates a new session
        ↓
Enters a product/growth question
        ↓
System retrieves relevant transcripts
        ↓
LLM generates grounded answer
        ↓
Answer and sources displayed
```

---

## 6.2 Follow-up Question

```text
Existing conversation
        ↓
User asks follow-up question
        ↓
Previous conversation context + relevant transcript context
        ↓
LLM generates response
        ↓
Response displayed in same session
```

Each session maintains independent conversation context.

---

## 6.3 Out-of-Domain / Insufficient Knowledge

```text
User question
      ↓
Transcript retrieval
      ↓
No sufficiently relevant content
      ↓
System does NOT invent an answer
      ↓
Explain that the transcript archive
does not contain sufficient information
```

Expected behavior:

> I do not have sufficient information in Lenny's podcast archive to answer this.

This behavior is important because the primary product requirement is trustworthy, grounded answers rather than generic AI answers.

---

## 6.4 Ship 30 for 30 Writing Flow

```text
User asks a question
        ↓
Relevant transcript content retrieved
        ↓
Grounded answer generated
        ↓
User requests article
        ↓
Ship 30 for 30 skill
        ↓
Approximately 1,250-word article
        ↓
Displayed in artifact/content view
```

The generated content should contain:

* Strong hook.
* Clear narrative progression.
* Short paragraphs.
* Headings.
* Bullets.
* Selective bold emphasis.
* Specific actionable takeaway.
* Claims grounded in transcript content.

These requirements come directly from the assignment.

---

## 6.5 Artifact Generation Flow

```text
User requests artifact
        ↓
LLM generates Markdown or HTML/CSS
        ↓
Backend identifies artifact
        ↓
Frontend opens Artifact Viewer
        ↓
Markdown → Markdown renderer
HTML/CSS → sandboxed iframe
```

Generated HTML must be treated as untrusted content and isolated from the main application.

---

# 7. Functional Requirements

## FR-1: Chat Sessions

The application must allow users to:

* Create a new chat session.
* Maintain independent conversation history.
* Continue an existing conversation.
* Store session timestamps.

---

## FR-2: Knowledge Ingestion

The system must ingest Lenny's Podcast transcripts from the specified public transcript repository.

The ingestion pipeline must:

1. Load transcript files.
2. Extract episode metadata.
3. Split transcripts into chunks.
4. Generate embeddings.
5. Store transcript chunks and embeddings.
6. Make them searchable through vector similarity.

The reference architecture recommends approximately 500–800 token chunks with 100-token overlap.

---

## FR-3: Retrieval

For every knowledge-based question:

1. Generate an embedding for the user's query.
2. Search the vector database.
3. Retrieve the most relevant transcript chunks.
4. Apply a similarity threshold.
5. Pass relevant context to the LLM.

The initial retrieval configuration will target approximately 4–6 relevant chunks.

---

## FR-4: Grounded Answers

The LLM must:

* Use retrieved transcript context.
* Avoid unsupported claims.
* Identify relevant sources.
* Acknowledge insufficient information.
* Maintain conversation context for follow-up questions.

---

## FR-5: Model Provider

The application must support:

### Local Provider

Ollama running an appropriate local model.

### Cloud Provider

At least one cloud provider such as Anthropic Claude or OpenAI.

The provider should be selectable through configuration and/or the application UI.

---

## FR-6: Streaming Responses

The backend should stream generated responses to the frontend so users can see the answer progressively rather than waiting for the complete response.

---

## FR-7: Ship 30 for 30 Skill

The application must provide a dedicated writing capability that transforms grounded transcript insights into approximately 1,250-word content.

The writing skill should encode the required structure and formatting instead of relying only on an unstructured generic prompt.

---

## FR-8: Artifact Viewer

The frontend must provide an artifact viewer capable of:

* Rendering Markdown.
* Rendering HTML/CSS.
* Displaying generated artifacts beside the chat.
* Handling loading and error states.
* Supporting a collapsible artifact panel.

---

## FR-9: Artifact Security

Generated HTML must be treated as untrusted.

The application should:

* Sanitize generated content.
* Render HTML inside a sandboxed iframe.
* Avoid granting same-origin access.
* Prevent generated content from accessing parent application storage, cookies, or DOM.

The reference implementation recommends `sandbox="allow-scripts"` without `allow-same-origin`.

---

## FR-10: Health Monitoring

The backend must expose a health endpoint capable of reporting the status of important dependencies such as:

* PostgreSQL.
* Ollama.
* Vector index/retrieval system.

---

# 8. Non-Functional Requirements

## Performance

Target:

* Local Ollama first-token latency: **< 4 seconds**.
* Vector retrieval should be fast enough to support interactive chat.
* Responses should stream progressively.

The <4-second first-token target is specified in the reference requirements.

---

## Reliability

The application must gracefully handle:

* Ollama unavailable.
* Cloud API unavailable.
* Missing API keys.
* Model timeout.
* Empty retrieval results.
* Database connection failure.
* Invalid user requests.

The application should return understandable errors instead of exposing raw exceptions to users.

---

## Security

The application must:

* Never commit API keys or secrets.
* Use environment variables for configuration.
* Treat generated HTML as untrusted.
* Sandbox artifact execution.
* Sanitize generated HTML.
* Avoid exposing database credentials to the frontend.

---

## Maintainability

The system should separate:

* API layer.
* Database layer.
* Retrieval layer.
* Embedding layer.
* LLM provider layer.
* Writing skills.
* Artifact generation.
* Frontend presentation.

This allows individual components to be modified without rewriting the entire application.

---

# 9. Success Metrics

The following initial targets will be used:

| Metric                          |                     Target |
| ------------------------------- | -------------------------: |
| Retrieval / citation accuracy   |                      ≥ 90% |
| Local model first-token latency |                < 4 seconds |
| Artifact XSS vulnerabilities    |                          0 |
| API health endpoint             |                  Available |
| Model switching                 | Works without code changes |
| Automated critical-path tests   |                    Passing |

The citation accuracy, local inference latency, and artifact safety targets are based on the assignment reference.

---

# 10. Assumptions

Because the assignment does not define every product detail, the following assumptions are made:

1. The transcript repository is the authoritative knowledge source for grounded answers.
2. Users do not require authentication for the evaluation version.
3. A single PostgreSQL database is sufficient for the evaluation environment.
4. Ollama will be available on the evaluator's machine for the local-model demonstration.
5. A cloud provider API key may be supplied through environment variables.
6. The initial system is designed for local evaluation rather than internet-scale traffic.
7. Transcript ingestion can be performed as a separate setup step rather than on every application startup.
8. The application will prioritize answer reliability over attempting to answer every question.

---

# 11. Scope Decisions and Trade-offs

## Local Model vs Cloud Model

### Decision

Support both.

### Reason

Ollama is required for the evaluation demo, while a cloud provider provides an alternative when local model quality or latency is insufficient.

### Trade-off

Local models reduce API cost and improve control but may have weaker reasoning quality and higher hardware requirements.

---

## RAG vs Sending Entire Transcripts

### Decision

Use RAG.

### Reason

Sending the entire transcript archive to the model would be inefficient and impractical as the knowledge base grows.

### Trade-off

RAG introduces embedding, chunking, retrieval, and relevance-threshold complexity.

---

## PostgreSQL + pgvector vs Separate Vector Database

### Decision

Use PostgreSQL with pgvector.

### Reason

The application already requires PostgreSQL for persistence, so using pgvector avoids introducing another database service.

### Trade-off

A specialized vector database may provide additional scaling capabilities, but it would increase infrastructure complexity for this assignment.

---

## Authentication

### Decision

Exclude authentication from the initial scope.

### Reason

Authentication is not required by the assignment and does not directly improve the core evaluation areas.

---

## Production Kubernetes

### Decision

Exclude Kubernetes.

### Reason

Docker Compose provides sufficient reproducibility for the evaluation while keeping deployment simple.

---

# 12. Risks

## Risk 1 — Hallucination

The LLM may generate claims that are not supported by retrieved transcripts.

### Mitigation

* Strict grounding prompt.
* Retrieval threshold.
* Source attribution.
* Explicit insufficient-information response.

---

## Risk 2 — Poor Retrieval

The correct transcript may not be retrieved.

### Mitigation

* Appropriate chunk size.
* Overlapping chunks.
* Vector similarity search.
* Retrieval evaluation tests.
* Tunable similarity threshold.

---

## Risk 3 — Local Model Quality

The local Ollama model may produce lower-quality responses than a cloud model.

### Mitigation

* Keep provider abstraction.
* Allow cloud provider fallback/configuration.
* Use a model appropriate for available hardware.

---

## Risk 4 — Local Model Latency

Running an LLM locally may be slow.

### Mitigation

* Use streaming.
* Select a model appropriate for available hardware.
* Monitor first-token latency.

---

## Risk 5 — Unsafe Generated HTML

Generated HTML may contain malicious or unsafe JavaScript.

### Mitigation

* Sanitize content.
* Render inside a sandboxed iframe.
* Do not grant `allow-same-origin`.

---

## Risk 6 — Dependency Failure

PostgreSQL, Ollama, or a cloud API may be unavailable.

### Mitigation

* Health endpoint.
* Timeouts.
* Structured error handling.
* Clear startup documentation.
* Graceful failure messages.

---

# 13. Acceptance Criteria

The product will be considered complete when:

### Chat

* [ ] User can create a chat session.
* [ ] User can send questions.
* [ ] Responses stream into the UI.
* [ ] Conversation history persists.
* [ ] Follow-up questions work.

### RAG

* [ ] Podcast transcripts are ingested.
* [ ] Transcript chunks are embedded.
* [ ] Embeddings are stored in pgvector.
* [ ] Relevant chunks are retrieved.
* [ ] Answers contain source attribution.
* [ ] Unsupported questions receive an insufficient-information response.

### LLM

* [ ] Ollama works locally.
* [ ] Cloud provider works.
* [ ] Provider can be switched without changing core code.
* [ ] Provider status is visible/documented.

### Ship 30 for 30

* [ ] Dedicated writing skill exists.
* [ ] Output targets approximately 1,250 words.
* [ ] Output contains a strong hook.
* [ ] Output is skimmable.
* [ ] Output contains actionable takeaways.
* [ ] Claims remain grounded in retrieved content.

### Artifacts

* [ ] Markdown artifacts render correctly.
* [ ] HTML/CSS artifacts render correctly.
* [ ] Artifact viewer appears beside the chat.
* [ ] Generated HTML is sanitized.
* [ ] HTML runs inside a sandboxed iframe.

### Operations

* [ ] Docker Compose starts the application.
* [ ] `.env.example` is provided.
* [ ] Health endpoint works.
* [ ] Structured logging exists.
* [ ] Critical automated tests pass.
* [ ] README contains setup and troubleshooting instructions.

---

# 14. Implementation Plan

## Phase 1 — Discovery

* Finalize PRD.
* Define architecture.
* Define UI/UX.
* Document assumptions and trade-offs.

## Phase 2 — Backend Foundation

* Create FastAPI application.
* Configure PostgreSQL.
* Create database models.
* Implement session APIs.
* Implement health endpoint.

## Phase 3 — Knowledge Base

* Download transcripts.
* Parse metadata.
* Chunk transcripts.
* Generate embeddings.
* Store vectors in pgvector.
* Implement retrieval.

## Phase 4 — AI Layer

* Create LLM provider interface.
* Implement Ollama provider.
* Implement cloud provider.
* Implement provider selection.
* Implement grounded QA.
* Implement streaming.

## Phase 5 — Skills

* Implement Ship 30 for 30 skill.
* Implement artifact generation.
* Implement citation handling.

## Phase 6 — Frontend

* Build chat interface.
* Add session handling.
* Add streaming responses.
* Add provider selector.
* Build Artifact Viewer.
* Implement Markdown rendering.
* Implement sandboxed HTML rendering.

## Phase 7 — Deployment & Testing

* Create Dockerfiles.
* Create Docker Compose.
* Add `.env.example`.
* Add automated tests.
* Add structured logging.
* Test failure scenarios.
* Complete README.
* Record demo.

---

# 15. Definition of Done

The Lenny Growth Assistant is considered ready for evaluation when a new developer can:

1. Clone the repository.
2. Configure the required environment variables.
3. Start the application using the documented setup command.
4. Access the frontend.
5. Create a chat session.
6. Ask a question about product or growth.
7. Receive a grounded answer with sources.
8. Switch between local and cloud models.
9. Generate a Ship 30 for 30-style article.
10. Generate and view a Markdown/HTML artifact.
11. Run the automated tests.
12. Diagnose common failures using the README and health endpoint.

The final deliverable should demonstrate not only technical functionality but also clear product judgment, architecture, grounding, deployment readiness, testing, UI/UX quality, and communication.

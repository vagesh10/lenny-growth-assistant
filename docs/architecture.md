# Architecture Specification

# The Lenny Growth Assistant

**Version:** 1.0
**Status:** Draft

---

## 1. Architecture Overview

The Lenny Growth Assistant is a full-stack Retrieval-Augmented Generation (RAG) application.

The system consists of:

* Next.js frontend
* FastAPI backend
* PostgreSQL database
* pgvector for vector similarity search
* Embedding model
* LLM provider abstraction
* Ollama for local inference
* Cloud LLM provider
* Ship 30 for 30 writing skill
* Artifact generation and sandboxed rendering
* Docker Compose for local deployment

### High-Level Architecture

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Next.js Frontend  │
                         │                     │
                         │ Chat UI             │
                         │ Session UI          │
                         │ Model Selector      │
                         │ Artifact Viewer     │
                         └──────────┬──────────┘
                                    │
                              HTTP / SSE
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Backend  │
                         │                     │
                         │ API Layer           │
                         │ Session Management  │
                         │ Chat Orchestrator   │
                         │ Skill Router        │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
      │ PostgreSQL    │     │ RAG Pipeline  │     │ LLM Providers │
      │ + pgvector    │     │               │     │               │
      │               │     │ Embeddings    │     │ Ollama        │
      │ Sessions      │     │ Retrieval     │     │ Cloud LLM     │
      │ Messages      │     │ Ranking       │     │               │
      │ Artifacts     │     └───────────────┘     └───────────────┘
      │ Transcripts   │
      └───────────────┘
```

---

# 2. Technology Stack

| Layer             | Technology                                |
| ----------------- | ----------------------------------------- |
| Frontend          | Next.js / React                           |
| Language          | TypeScript                                |
| Styling           | Tailwind CSS                              |
| Backend           | FastAPI                                   |
| Backend Language  | Python 3.11+                              |
| API Server        | Uvicorn                                   |
| Validation        | Pydantic v2                               |
| Database          | PostgreSQL                                |
| Vector Search     | pgvector                                  |
| ORM               | SQLAlchemy                                |
| Embeddings        | sentence-transformers / Ollama embeddings |
| Local LLM         | Ollama                                    |
| Cloud LLM         | Anthropic Claude or OpenAI                |
| Markdown          | react-markdown + remark-gfm               |
| HTML Sanitization | DOMPurify                                 |
| Containerization  | Docker + Docker Compose                   |
| Testing           | pytest                                    |

The stack follows the technical requirements in the assignment reference.

---

# 3. System Components

## 3.1 Frontend

The frontend is responsible for:

* Chat interface.
* Session selection.
* Message history.
* Streaming response display.
* Model/provider selection.
* Artifact viewer.
* Loading and error states.

The frontend communicates with the backend through REST APIs and Server-Sent Events (SSE) for streaming responses.

---

## 3.2 FastAPI Backend

The backend is the primary application orchestrator.

Responsibilities:

* Validate incoming requests.
* Manage chat sessions.
* Store messages.
* Retrieve transcript context.
* Select the LLM provider.
* Execute the appropriate skill.
* Stream responses.
* Store generated artifacts.
* Expose health information.
* Handle errors and logging.

---

## 3.3 PostgreSQL

PostgreSQL is used for relational application data and transcript storage.

It stores:

* Sessions.
* Messages.
* Artifacts.
* Transcript metadata.
* Transcript chunks.
* Vector embeddings.

The pgvector extension provides vector similarity search inside PostgreSQL.

---

# 4. Database Architecture

## 4.1 Session

Represents an independent user conversation.

```text
Session
---------
id
title
created_at
updated_at
```

### Fields

| Field      | Type      | Description                  |
| ---------- | --------- | ---------------------------- |
| id         | UUID      | Unique session identifier    |
| title      | VARCHAR   | Human-readable session title |
| created_at | TIMESTAMP | Creation time                |
| updated_at | TIMESTAMP | Last update time             |

---

## 4.2 Message

Stores individual messages within a session.

```text
Message
---------
id
session_id
role
content
sources
created_at
```

### Fields

| Field      | Type      | Description                  |
| ---------- | --------- | ---------------------------- |
| id         | UUID      | Message identifier           |
| session_id | UUID      | Parent session               |
| role       | VARCHAR   | user / assistant             |
| content    | TEXT      | Message content              |
| sources    | JSONB     | Retrieved transcript sources |
| created_at | TIMESTAMP | Creation time                |

Relationship:

```text
Session
   │
   ├── Message
   ├── Message
   └── Message
```

---

## 4.3 Artifact

Stores generated artifacts.

```text
Artifact
---------
id
message_id
artifact_type
content
created_at
```

### Fields

| Field         | Type      | Description                         |
| ------------- | --------- | ----------------------------------- |
| id            | UUID      | Artifact identifier                 |
| message_id    | UUID      | Message that generated the artifact |
| artifact_type | VARCHAR   | markdown / html                     |
| content       | TEXT      | Generated artifact                  |
| created_at    | TIMESTAMP | Creation time                       |

---

## 4.4 Transcript Chunk

Represents a searchable section of a podcast transcript.

```text
TranscriptChunk
----------------
id
episode_title
guest_name
publication_date
timestamp_ref
chunk_text
embedding
metadata
```

### Fields

| Field            | Type   | Description               |
| ---------------- | ------ | ------------------------- |
| id               | UUID   | Chunk identifier          |
| episode_title    | TEXT   | Podcast episode           |
| guest_name       | TEXT   | Guest                     |
| publication_date | DATE   | Episode publication date  |
| timestamp_ref    | TEXT   | Timestamp/topic reference |
| chunk_text       | TEXT   | Transcript content        |
| embedding        | VECTOR | Generated embedding       |
| metadata         | JSONB  | Additional metadata       |

---

# 5. Database Relationships

```text
┌──────────────┐
│   Session    │
└──────┬───────┘
       │ 1
       │
       │ many
       ▼
┌──────────────┐
│   Message    │
└──────┬───────┘
       │ 1
       │
       │ many
       ▼
┌──────────────┐
│   Artifact   │
└──────────────┘


┌────────────────────┐
│ TranscriptChunk    │
│                    │
│ embedding          │
│ metadata           │
│ transcript text    │
└────────────────────┘
```

Transcript chunks are independently searchable through vector similarity.

---

# 6. Knowledge Ingestion Architecture

Transcript ingestion is performed separately from normal user requests.

```text
Lenny Transcript Repository
            │
            ▼
   Download Transcript
            │
            ▼
      Parse Metadata
            │
            ▼
       Split Chunks
            │
            ▼
    Generate Embeddings
            │
            ▼
 PostgreSQL + pgvector
```

The ingestion pipeline should extract:

* Guest name.
* Episode title.
* Publication date.
* Timestamp/topic references.
* Transcript text.

The reference requirements specify recursive chunking with a target of approximately 500–800 tokens and 100-token overlap.

---

# 7. Embedding Architecture

Each transcript chunk is converted into a vector representation.

```text
Transcript Chunk
       │
       ▼
Embedding Model
       │
       ▼
Vector
       │
       ▼
PostgreSQL / pgvector
```

The initial implementation can use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

or an appropriate Ollama embedding model.

The same embedding strategy must be used when generating query embeddings so that query and transcript vectors exist in the same vector space.

---

# 8. RAG Retrieval Architecture

The RAG pipeline is the central knowledge component.

## Query Flow

```text
User Question
      │
      ▼
Generate Query Embedding
      │
      ▼
pgvector Similarity Search
      │
      ▼
Retrieve Top K Chunks
      │
      ▼
Apply Similarity Threshold
      │
      ├───────────────┐
      │               │
      ▼               ▼
Relevant          Insufficient
Context           Context
      │               │
      ▼               ▼
   LLM             Safe fallback
      │
      ▼
Grounded Answer
      │
      ▼
Source Attribution
```

The initial retrieval target is approximately 4–6 relevant chunks.

A similarity threshold will be used to prevent weakly related transcript content from being presented as reliable evidence.

---

# 9. Similarity Search

The application will use cosine similarity for retrieval.

Conceptually:

```sql
SELECT
    episode_title,
    guest_name,
    chunk_text,
    timestamp_ref,
    1 - (embedding <=> :query_vector) AS similarity_score
FROM transcript_chunks
WHERE 1 - (embedding <=> :query_vector) >= :threshold
ORDER BY similarity_score DESC
LIMIT :top_k;
```

An HNSW index should be used to improve vector search performance as the transcript collection grows.

---

# 10. Grounding Strategy

Retrieved transcript chunks are passed to the LLM as explicit context.

The system prompt will establish rules such as:

```text
You are the Lenny Growth Assistant.

Answer using only the supplied transcript context.

Do not invent information.

If the context does not contain enough information,
say that the Lenny podcast archive does not provide
sufficient information to answer the question.

Attribute claims to the relevant episode and guest.
```

The answer should contain source references such as:

```text
[Episode: Guest Name, Timestamp/Topic]
```

This ensures that users can understand where the information originated.

---

# 11. LLM Provider Architecture

The application uses a provider abstraction.

```text
                 BaseLLMProvider
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      OllamaProvider        CloudProvider
             │                     │
             ▼                     ▼
          Ollama             Claude/OpenAI
```

The application should interact with the common interface rather than directly calling a specific provider.

---

# 12. Provider Interface

The common interface exposes asynchronous generation and streaming behavior.

Conceptually:

```python
class BaseLLMProvider:

    async def generate_response(
        self,
        messages,
        system_prompt,
        temperature=0.3
    ):
        ...
```

Concrete implementations:

```text
backend/app/providers/
├── base.py
├── ollama_provider.py
└── cloud_provider.py
```

The provider abstraction allows the rest of the application to remain independent of the underlying model.

The assignment explicitly requires model switching without modifying application code.

---

# 13. Model Selection

The provider can be selected through configuration.

Example:

```env
DEFAULT_LLM_PROVIDER=ollama
```

Supported values:

```text
ollama
cloud
```

The frontend may also expose a provider selector.

```text
User
 │
 ▼
Provider Selector
 │
 ├── Ollama
 │
 └── Cloud
       │
       ▼
FastAPI
       │
       ▼
Provider Factory
       │
       ▼
Selected Provider
```

---

# 14. Chat Request Architecture

Example request:

```http
POST /api/chat
Content-Type: application/json
```

Request:

```json
{
  "session_id": "uuid",
  "message": "How can I improve user retention?",
  "mode": "default",
  "provider": "ollama"
}
```

Processing:

```text
Request
  ↓
Validate request
  ↓
Load session
  ↓
Generate query embedding
  ↓
Retrieve transcript chunks
  ↓
Build grounded prompt
  ↓
Select provider
  ↓
Generate response
  ↓
Stream response
  ↓
Persist assistant message
```

---

# 15. API Architecture

## POST `/api/sessions`

Creates a new chat session.

### Response

```json
{
  "id": "uuid",
  "title": "New Chat",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## GET `/api/sessions/{session_id}`

Returns session information and message history.

---

## POST `/api/chat`

Processes a user question and streams the response.

Supported modes:

```text
default
ship30
```

Supported providers:

```text
ollama
cloud
```

---

## GET `/api/health`

Returns application dependency health.

Example:

```json
{
  "status": "healthy",
  "database": "healthy",
  "ollama": "healthy",
  "vector_index": "healthy"
}
```

The required API surface is based on the reference architecture.

---

# 16. Streaming Architecture

Responses will use Server-Sent Events (SSE).

```text
FastAPI
   │
   │ text/event-stream
   ▼
Next.js
   │
   ▼
Update message bubble
```

Example event sequence:

```text
data: {"type":"status","content":"Retrieving transcripts..."}

data: {"type":"token","content":"One"}

data: {"type":"token","content":" approach"}

data: {"type":"token","content":" is"}

data: [DONE]
```

This allows the frontend to display the answer incrementally.

---

# 17. Ship 30 for 30 Skill Architecture

The writing capability is isolated as a dedicated skill.

```text
User Request
      │
      ▼
Retrieve Grounded Context
      │
      ▼
Ship 30 Skill
      │
      ▼
Structured Prompt
      │
      ▼
LLM Provider
      │
      ▼
~1,250 Word Essay
```

The skill should enforce:

* Strong hook.
* Clear narrative.
* Short paragraphs.
* Markdown headings.
* Bold anchor points.
* Bullets.
* Actionable conclusion.
* Grounding in transcript context.

---

# 18. Artifact Architecture

The assistant can produce two artifact types:

```text
markdown
html
```

Generated content is detected and passed to the appropriate frontend renderer.

```text
LLM Response
     │
     ▼
Artifact Detection
     │
     ├──────────────┐
     ▼              ▼
 Markdown          HTML
     │              │
     ▼              ▼
react-markdown   DOMPurify
                    │
                    ▼
               Sandboxed iframe
```

---

# 19. Artifact Security

Generated HTML is untrusted.

The application will use:

```html
<iframe sandbox="allow-scripts">
```

The following capability is intentionally not granted:

```text
allow-same-origin
```

This limits the generated document's ability to interact with the parent application's origin, storage, cookies, and DOM.

The HTML should also be sanitized before being inserted into `srcDoc`.

Security flow:

```text
Generated HTML
      │
      ▼
DOMPurify
      │
      ▼
Sanitized HTML
      │
      ▼
Sandboxed iframe
      │
      ▼
Rendered Artifact
```

This follows the security expectations specified in the assignment.

---

# 20. Frontend Component Architecture

```text
frontend/src/
│
├── app/
│   ├── layout.tsx
│   └── page.tsx
│
├── components/
│   │
│   ├── Chat/
│   │   ├── ChatPane.tsx
│   │   ├── MessageItem.tsx
│   │   └── ModelSelector.tsx
│   │
│   └── Artifact/
│       ├── ArtifactViewer.tsx
│       └── SandboxedIframe.tsx
│
├── hooks/
│   └── useChatStream.ts
│
└── lib/
    └── api.ts
```

---

# 21. Backend Component Architecture

```text
backend/app/
│
├── main.py
├── config.py
├── database.py
│
├── models/
│   ├── db_models.py
│   └── schemas.py
│
├── providers/
│   ├── base.py
│   ├── ollama_provider.py
│   └── cloud_provider.py
│
├── rag/
│   ├── retriever.py
│   └── embeddings.py
│
├── skills/
│   ├── ship30_writer.py
│   └── artifact_generator.py
│
└── api/
    ├── sessions.py
    ├── chat.py
    └── health.py
```

This separation keeps retrieval, providers, skills, APIs, and persistence independently maintainable.

---

# 22. Request Processing Sequence

For a normal question:

```text
1. User submits question
          ↓
2. Frontend sends POST /api/chat
          ↓
3. FastAPI validates request
          ↓
4. Session is loaded
          ↓
5. Query embedding is generated
          ↓
6. pgvector retrieves relevant chunks
          ↓
7. Similarity threshold is checked
          ↓
8. Grounded prompt is constructed
          ↓
9. Provider is selected
          ↓
10. LLM begins streaming
          ↓
11. Frontend displays tokens
          ↓
12. Sources are displayed
          ↓
13. Final assistant message is persisted
```

---

# 23. Failure Handling

The system must fail gracefully.

## Database unavailable

```text
Request
  ↓
Database failure
  ↓
Structured error
  ↓
HTTP 503
```

---

## Ollama unavailable

```text
Request
  ↓
Ollama connection failure
  ↓
Return provider error
  ↓
Offer configured cloud provider if available
```

---

## Empty retrieval

```text
Question
  ↓
Vector search
  ↓
No relevant chunks
  ↓
Do not call the model for unsupported knowledge
  OR
Use a grounded fallback response
```

The exact behavior should prioritize preventing unsupported answers.

---

## Model timeout

```text
LLM request
   ↓
Timeout
   ↓
Cancel stream
   ↓
Return clear error
   ↓
Log failure
```

---

# 24. Observability

Structured logs should provide enough information to diagnose:

* Request failures.
* Retrieval failures.
* Retrieval latency.
* Number of retrieved chunks.
* Similarity scores.
* Selected LLM provider.
* Model latency.
* Database failures.
* Artifact processing failures.

Example structured event:

```json
{
  "event": "rag_retrieval",
  "session_id": "uuid",
  "top_k": 5,
  "results": 4,
  "latency_ms": 142
}
```

Sensitive information such as API keys must never be logged.

---

# 25. Configuration Architecture

Configuration should be environment-based.

Example:

```env
DATABASE_URL=postgresql+asyncpg://...
DEFAULT_LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

ANTHROPIC_API_KEY=
OPENAI_API_KEY=

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

A safe `.env.example` must be committed.

Actual secrets must not be committed to GitHub.

---

# 26. Deployment Architecture

Docker Compose will orchestrate the application.

```text
                    Docker Compose
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   PostgreSQL         Backend          Frontend
   + pgvector         FastAPI          Next.js
        │                │
        │                ▼
        │              Ollama
        │
        ▼
    Persistent
      Volume
```

The reference deployment specifies PostgreSQL + pgvector, FastAPI, frontend, and optionally Ollama as separate services.

---

# 27. Docker Services

## Database

```text
Service: db
Image: pgvector/pgvector:pg16
Port: 5432
```

Responsible for:

* Application data.
* Transcript data.
* Vector embeddings.

---

## Backend

```text
Service: backend
Framework: FastAPI
Port: 8000
```

Responsible for:

* APIs.
* RAG.
* LLM routing.
* Persistence.
* Streaming.

---

## Frontend

```text
Service: frontend
Framework: Next.js
Port: 3000
```

Responsible for:

* User interface.
* Chat.
* Artifacts.
* Provider selection.

---

## Ollama

Ollama can run locally on the host machine or as an optional container depending on the deployment environment.

The backend communicates with the configured Ollama endpoint.

---

# 28. Deployment Startup

The intended developer experience is:

```bash
docker-compose up
```

Then:

```text
Frontend:
http://localhost:3000

Backend:
http://localhost:8000

Health:
http://localhost:8000/api/health
```

The exact deployment configuration will be documented in the README.

---

# 29. Security Boundaries

```text
                 Browser
                    │
                    │
             ┌──────▼──────┐
             │  Frontend   │
             └──────┬──────┘
                    │
                    │ API
                    ▼
             ┌─────────────┐
             │   Backend   │
             └──────┬──────┘
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Database       Ollama      Cloud API
```

Security principles:

* Secrets remain server-side.
* Frontend never receives API keys.
* Database credentials remain server-side.
* Generated HTML is isolated.
* Inputs are validated.
* Errors do not expose sensitive infrastructure details.

---

# 30. Testing Architecture

Testing will focus on critical system behavior.

## Retrieval Tests

Verify:

* Relevant chunks are returned.
* Similarity ordering is correct.
* Threshold filtering works.
* Empty results are handled.

## Provider Tests

Verify:

* Ollama provider works.
* Cloud provider works.
* Provider selection works.
* Invalid provider is rejected.
* Provider timeout is handled.

## API Tests

Verify:

* Sessions can be created.
* Messages can be persisted.
* Chat endpoint works.
* Health endpoint works.
* Invalid requests return structured errors.

## Artifact Tests

Verify:

* Markdown renders.
* HTML is sanitized.
* Sandbox configuration is correct.
* Artifact persistence works.

---

# 31. Architectural Trade-offs

## PostgreSQL + pgvector

**Chosen because:** It provides relational persistence and vector search in one system.

**Alternative:** Dedicated vector database.

**Trade-off:** Simpler infrastructure at the cost of less specialized vector infrastructure.

---

## RAG

**Chosen because:** Only relevant transcript sections need to be sent to the LLM.

**Alternative:** Send complete transcripts to a long-context model.

**Trade-off:** RAG requires chunking and retrieval quality management.

---

## Provider Abstraction

**Chosen because:** Local and cloud models can be switched without rewriting business logic.

**Trade-off:** Adds an abstraction layer and requires consistent behavior across providers.

---

## SSE

**Chosen because:** It is simple and appropriate for one-way token streaming from backend to browser.

**Trade-off:** It is less flexible than a bidirectional WebSocket architecture, but WebSockets are unnecessary for this use case.

---

## Docker Compose

**Chosen because:** It provides reproducible local deployment with relatively low operational complexity.

**Alternative:** Kubernetes.

**Trade-off:** Compose is less suitable for large-scale orchestration but is appropriate for the assignment's evaluation environment.

---

# 32. End-to-End Architecture

The final system can be summarized as:

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │    Next.js      │
                  │    Frontend     │
                  └────────┬────────┘
                           │
                       REST / SSE
                           │
                           ▼
                  ┌─────────────────┐
                  │     FastAPI     │
                  │    Backend      │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       PostgreSQL        RAG Layer     LLM Layer
       + pgvector           │              │
            │               │        ┌─────┴─────┐
            │               │        │           │
            │               │        ▼           ▼
            │               │     Ollama    Cloud LLM
            │               │
            │               ▼
            │        Relevant Context
            │               │
            └───────────────┼──────────────┐
                            ▼              │
                         Grounded          │
                          Answer           │
                            │              │
                   ┌────────┴────────┐     │
                   ▼                 ▼     │
               Chat UI          Artifact UI
                                     │
                           ┌─────────┴─────────┐
                           ▼                   ▼
                       Markdown          HTML/CSS
                                           │
                                      DOMPurify
                                           │
                                   Sandboxed iframe
```

---

# 33. Architecture Principles

The implementation will follow these principles:

1. **Grounded by default** — transcript evidence is required for knowledge answers.
2. **Fail safely** — lack of evidence should produce a clear fallback rather than hallucination.
3. **Provider independent** — application logic should not depend on one LLM vendor.
4. **Separation of concerns** — APIs, retrieval, providers, skills, and persistence remain separate.
5. **Secure by design** — generated HTML is treated as untrusted.
6. **Observable** — important operations and failures are logged.
7. **Reproducible** — Docker Compose provides a repeatable development environment.
8. **Simple where possible** — avoid infrastructure and features that do not improve the required product.

---

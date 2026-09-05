# Lenny Growth Assistant

A grounded AI growth assistant built around Lenny's podcast transcripts. The application uses retrieval-augmented generation (RAG) to answer product and growth questions from the transcript knowledge base, supports conversational follow-ups, generates artifacts, and produces a structured 30-day Ship30 plan.

## Features

- Grounded Q&A over Lenny's podcast transcripts
- Retrieval-Augmented Generation using vector search
- Transcript chunks with timestamp/episode metadata
- Conversational sessions with persisted messages
- Streaming chat responses
- Source citations for retrieved transcript evidence
- Safe fallback when the knowledge base does not contain enough evidence
- Local LLM support through Ollama
- Optional OpenAI provider
- Artifact generation:
  - Markdown
  - HTML
  - CSS
- Sandboxed HTML/CSS artifact preview
- DOM sanitization for generated HTML
- Dedicated Ship30 30-day plan generator
- Strict validation for exactly Day 1 through Day 30
- PostgreSQL + pgvector persistence
- Docker Compose setup
- FastAPI Swagger documentation
- Automated tests for retrieval, model switching, and Ship30 validation

## Architecture

```text
                    ┌──────────────────────┐
                    │     Next.js UI       │
                    │  Chat / Artifacts    │
                    │     / Ship30         │
                    └──────────┬───────────┘
                               │ HTTP / SSE
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI         │
                    │ Sessions / Chat /    │
                    │ Artifacts / Health   │
                    └───────┬───────┬──────┘
                            │       │
                   Retrieval│       │LLM
                            │       │
                            ▼       ▼
                  ┌────────────┐  ┌─────────────┐
                  │ PostgreSQL │  │   Ollama    │
                  │ + pgvector │  │ / OpenAI    │
                  └────────────┘  └─────────────┘
                            ▲
                            │
                  ┌──────────────────┐
                  │ Lenny Transcripts│
                  │ 500-token chunks │
                  │ 100-token overlap│
                  └──────────────────┘
Tech Stack
Frontend
Next.js
React
TypeScript
Tailwind CSS
react-markdown
remark-gfm
DOMPurify
Backend
Python
FastAPI
SQLAlchemy
PostgreSQL
pgvector
Sentence Transformers
Ollama
OpenAI API
Infrastructure
Docker
Docker Compose
PostgreSQL with pgvector
Knowledge Base

The application uses Lenny's podcast transcript dataset.

Transcripts are parsed and divided into approximately 500-token chunks with 100-token overlap. Embeddings are generated using:

sentence-transformers/all-MiniLM-L6-v2

The retriever performs vector similarity search and applies a small lexical reranking signal. Weak or unrelated results are filtered using a similarity threshold.

The ingestion pipeline currently contains more than 14,000 transcript chunks in the development database.

RAG Flow
User Question
      │
      ▼
Build Retrieval Query
      │
      ▼
Generate Query Embedding
      │
      ▼
pgvector Similarity Search
      │
      ▼
Top Relevant Transcript Chunks
      │
      ▼
Grounded Prompt
      │
      ▼
Ollama / OpenAI
      │
      ▼
Answer + Sources

Conversation history can be used to resolve follow-up references, but previous assistant responses are not treated as evidence.

If retrieved transcript evidence is insufficient, the assistant falls back instead of inventing factual claims.

Model Providers

The application supports two model providers.

Ollama

Ollama is the default local provider.

Example configuration:

DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

Make sure Ollama is running and the selected model is available locally.

OpenAI

OpenAI can be selected as an alternative provider.

OPENAI_API_KEY=your_api_key

The application does not require an OpenAI key when using Ollama.

Environment Variables

Copy the example environment file:

Copy-Item .env.example .env

Important variables include:

DATABASE_URL=postgresql+asyncpg://postgres:password123@localhost:5433/lenny_assistant

DEFAULT_LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

OPENAI_API_KEY=

Never commit .env or API keys to GitHub.

Running with Docker Compose

The complete application can be started with:

docker compose up -d

Check services:

docker compose ps

Expected services:

lenny_postgres
lenny_backend
lenny_frontend
Application

Frontend:

http://localhost:3000

Backend:

http://localhost:8000

Swagger API documentation:

http://localhost:8000/docs

Health check:

http://localhost:8000/api/health

Example health response:

{
  "status": "healthy",
  "database": "healthy"
}

Stop the stack:

docker compose down
Local Development
Backend

Create and activate a virtual environment:

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Start FastAPI:

python -m uvicorn app.main:app --reload --port 8000
Frontend
cd frontend
npm install
npm run dev

The frontend runs on:

http://localhost:3000
Transcript Ingestion

The transcript dataset is stored under:

backend/data/lenny-transcripts/

The ingestion pipeline:

Reads transcript files
Parses transcript text and metadata
Splits transcripts into token-aware chunks
Generates embeddings
Stores chunks and vectors in PostgreSQL/pgvector

The target chunk configuration is approximately:

Chunk size: 500 tokens
Overlap:    100 tokens
API Endpoints
Health
GET /api/health
Sessions
POST /api/sessions
GET /api/sessions/{session_id}
Chat
POST /api/chat
POST /api/chat/stream
Artifacts
POST /api/artifacts
POST /api/artifacts/ship30

Supported artifact types:

markdown
html
css
Ship30

The application includes a dedicated Ship30 generator.

The generator is designed to produce exactly:

Day 1
Day 2
...
Day 30

Validation rejects:

Missing days
Duplicate days
Day 31 or later
Grouped ranges such as Days 1-5
Invalid/non-30-day structures

Generation retries once when the model output fails validation.

Artifact Security

Generated HTML is sanitized before rendering.

HTML/CSS previews are rendered inside a sandboxed iframe. The iframe is configured to avoid granting unnecessary same-origin access.

This reduces the risk of generated artifact content accessing the main application context.

Testing

Run the test suite from the project root:

cd backend
python -m pytest

Tests cover:

Retrieval relevance
Out-of-domain retrieval fallback
LLM provider selection
Invalid provider handling
Ship30 validation
Missing/duplicate days
Day 31 rejection
Grouped day rejection
Project Structure
lenny-growth-assistant/
│
├── agent_transcripts/
│   └── development.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── llm/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── data/
│   │   └── lenny-transcripts/
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── design.md
│
├── frontend/
│   ├── app/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── package.json
│   └── package-lock.json
│
├── .env.example
├── .gitignore
└── docker-compose.yml
Operational Resilience

The application is designed to handle common operational failures:

Missing cloud API keys
Ollama unavailable
Model generation failures/timeouts
Empty retrieval results
Database failures
Invalid generated Ship30 output

The system prefers a grounded fallback over unsupported factual claims.

Documentation

Additional project documentation:

docs/PRD.md — product requirements and user flows
docs/architecture.md — system architecture and technical decisions
docs/design.md — frontend and interaction design
agent_transcripts/development.md — development/debugging decisions
Demo

The recommended demo flow is:

Open the application
Ask a Lenny growth/product question
Show the grounded answer and transcript sources
Ask a follow-up question
Demonstrate the grounded fallback when evidence is insufficient
Generate a Markdown artifact
Generate an HTML/CSS artifact and preview it
Generate the 30-day Ship30 plan
Briefly show the provider selection and Dockerized architecture
Design Tradeoffs
Local-first model execution

Ollama is the default because it allows the application to run without requiring a paid cloud API.

OpenAI is implemented as an optional provider for environments where cloud inference is preferred.

Vector retrieval

pgvector keeps embeddings close to the application database and avoids introducing another infrastructure dependency.

Strict grounding

The assistant is intentionally conservative. When transcript evidence is insufficient, it should say so rather than manufacture an answer.

Generated artifacts

Artifacts are treated as separate generated outputs and rendered through a controlled viewer rather than injecting arbitrary HTML directly into the main application DOM.

Future Improvements

Potential improvements include:

Better hybrid retrieval/reranking
More robust transcript metadata normalization
Background ingestion jobs
Additional LLM providers
More comprehensive integration tests
Production deployment with managed PostgreSQL
Evaluation datasets for retrieval and answer faithfulness
Improved Ship30 content diversity and editorial quality
License

This project was created as a take-home engineering assignment.


### Then save and push it

From your project root:

```powershell
notepad README.md

Paste the README above, save, close Notepad.

Then:

git add README.md
git commit -m "Add project README"
git push

Finally:

git status

You want:

nothing to commit, working tree clean
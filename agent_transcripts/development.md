# Agent Development Transcript

## 1. Streaming Generation Failure

### Problem
Non-streaming Ollama generation worked, but the streaming endpoint initially returned an incorrect fallback/empty response.

### Investigation
The streaming path was tested independently from the normal generation path.

### Correction
The Ollama generation request was updated to use deterministic generation with:

- temperature = 0
- streaming enabled
- JSONL response parsing
- explicit handling of the done event

### Result
Direct Ollama streaming worked and the frontend could consume the streamed response.

---

## 2. Retrieval Quality

### Problem
Some semantic retrieval results were relevant but not always the strongest lexical matches.

### Investigation
Embedding similarity scores were inspected for onboarding queries.

### Correction
The retriever was kept vector-based but added a small keyword-match reranking bonus. A similarity threshold was also introduced to prevent weak results from reaching the model.

### Result
Relevant transcript chunks were returned while empty/out-of-domain queries could fall back safely.

---

## 3. Follow-up Grounding

### Problem
A follow-up question such as asking about activation after an onboarding discussion could cause the model to rely on previous assistant text instead of transcript evidence.

### Correction
Conversation history is used only to resolve references. It is explicitly treated as non-evidence. Factual claims must come from retrieved transcript sources.

### Result
Follow-up questions that lack sufficient transcript evidence produce a grounded fallback instead of invented information.

---

## 4. Ship30 Validation

### Problem
Initial Ship30 generations did not consistently satisfy the exact Day 1–30 format.

### Correction
A strict validator was added requiring:

- exactly Day 1 through Day 30
- no missing days
- no duplicate days
- no Day 31
- no grouped ranges such as Days 1–5

Generation retries once when validation fails.

### Result
The generated Ship30 artifact successfully produces exactly 30 individual days.

---

## 5. Artifact Viewer Expansion

### Problem
The initial artifact workflow focused on Markdown.

### Correction
The artifact API and frontend were extended to support:

- Markdown
- HTML
- CSS

HTML/CSS previews are rendered inside sandboxed iframes with sanitization.

### Result
All three artifact types were tested successfully in the UI.

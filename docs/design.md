# Design Specification

# The Lenny Growth Assistant

**Version:** 1.0
**Status:** Draft

---

## 1. Design Overview

The Lenny Growth Assistant is designed as a focused AI workspace for Product Managers and Growth Leaders.

The primary interaction is conversational: users ask questions and receive grounded answers from Lenny's Podcast transcripts.

The interface also provides an Artifact Viewer that allows users to inspect generated Markdown or HTML/CSS without leaving the application.

The design prioritizes:

* Clarity.
* Speed.
* Source transparency.
* Minimal cognitive load.
* Useful feedback during AI processing.
* Safe artifact rendering.
* Responsive behavior.
* Accessibility.

---

# 2. Design Goals

## 2.1 Make the Chat the Primary Experience

The user should immediately understand:

> "I can ask a product or growth question here."

The chat should therefore occupy the majority of the available screen.

---

## 2.2 Make Sources Visible

Because the assistant is based on retrieved podcast transcripts, source information should not be hidden.

Each grounded response should provide an understandable source reference.

Example:

```text
Based on insights from several product leaders, one useful approach
is to identify the user's core recurring value before optimizing
secondary engagement.

Sources

[Episode: Brian Balfour, Growth Loops]
[Episode: Elena Verna, Product Growth]
```

---

## 2.3 Make AI State Understandable

AI applications can feel broken if the interface gives no feedback while waiting.

The UI should communicate states such as:

```text
Retrieving transcripts...
Generating answer...
Generating article...
Rendering artifact...
```

The user should never have to guess whether the application is still working.

---

# 3. Information Architecture

The application has three major areas:

```text
┌───────────────────────────────────────────────────────┐
│ Header                                                │
├─────────────────────────────┬─────────────────────────┤
│                             │                         │
│                             │                         │
│        Chat Area             │    Artifact Viewer     │
│                             │                         │
│                             │                         │
│                             │                         │
├─────────────────────────────┤                         │
│ Message Input               │                         │
└─────────────────────────────┴─────────────────────────┘
```

### Primary Areas

1. Header / application controls.
2. Chat pane.
3. Artifact pane.

---

# 4. Main Layout

The desktop interface uses a two-column layout.

```text
┌──────────────────────────────────────────────────────────────┐
│ Lenny Growth Assistant          [Ollama ▼]       [New Chat]  │
├────────────────────────────────┬─────────────────────────────┤
│                                │                             │
│ Chat                           │ Artifact                    │
│                                │                             │
│ User                           │                             │
│ How can I improve retention?   │     No artifact selected    │
│                                │                             │
│ Assistant                      │                             │
│ Based on the podcast...        │                             │
│                                │                             │
│ Sources                        │                             │
│ • Episode / Guest              │                             │
│                                │                             │
│                                │                             │
│                                │                             │
├────────────────────────────────┤                             │
│ Ask a product question...  [→] │                             │
└────────────────────────────────┴─────────────────────────────┘
```

The artifact panel can be collapsed when the user wants a larger chat area.

The assignment requires a responsive two-column experience with a collapsible artifact drawer.

---

# 5. Header

The header should contain:

```text
Lenny Growth Assistant
```

and the primary controls:

```text
[Model: Ollama ▼]
[New Chat]
```

Optional controls can include:

```text
[Artifact]
[Settings]
```

The header should remain visually simple.

The user should not need to understand technical concepts such as embeddings, vector databases, or retrieval pipelines.

---

# 6. Chat Pane

The Chat Pane is the primary workspace.

It contains:

1. Session information.
2. Message history.
3. Streaming responses.
4. Source information.
5. Message input.

---

# 7. Empty Chat State

When a new session is created, the user should see a helpful starting state.

Example:

```text
        Lenny Growth Assistant

Ask questions about product management,
growth, startups, and product strategy
using insights from Lenny's Podcast.

Try asking:

"What are effective user retention strategies?"

"How should a startup prioritize features?"

"How do successful growth teams identify
their biggest growth constraint?"
```

The empty state should encourage useful questions without pretending that every question can be answered.

---

# 8. Message Design

User and assistant messages should be visually distinguishable.

Example:

```text
YOU

How should I approach product-market fit?


LENNY GROWTH ASSISTANT

The podcast discussions suggest that product-market
fit should be evaluated through evidence of repeated
customer value rather than relying only on top-line
growth metrics.

Sources

[Episode: Guest Name, Topic]
[Episode: Guest Name, Topic]
```

Assistant messages should support:

* Markdown.
* Headings.
* Lists.
* Bold text.
* Code blocks where appropriate.
* Source references.

---

# 9. Streaming State

When the LLM is generating a response, the message should appear progressively.

Example:

```text
LENNY GROWTH ASSISTANT

Product-market fit is often evaluated...
                                      █
```

The cursor/loading indicator communicates that generation is still in progress.

A status indicator can appear above the response:

```text
● Retrieving transcripts
```

followed by:

```text
● Generating response
```

and finally:

```text
✓ Complete
```

---

# 10. Retrieval Status

Before model generation begins, the UI should communicate retrieval.

Example:

```text
Searching Lenny's Podcast...
Found 5 relevant transcript sections.
```

This improves transparency and makes the RAG process understandable without exposing unnecessary technical details.

---

# 11. Source Display

Sources should appear directly below the grounded response.

Example:

```text
Sources
────────────────────────────────

Episode: [Guest Name]
Topic: Product Strategy
Timestamp: 34:12

Episode: [Guest Name]
Topic: Growth Loops
Timestamp: 18:47
```

Sources should be visually secondary to the answer but easy to identify.

The purpose is to allow users to understand which transcript material informed the response.

---

# 12. Insufficient Information State

When retrieval does not find sufficiently relevant information, the UI should clearly communicate the limitation.

Example:

```text
I couldn't find sufficient information in
Lenny's Podcast archive to answer this question.

Try asking about:
• Product strategy
• Growth
• Retention
• Product-market fit
```

The interface must not display a normal-looking AI answer when the system has determined that the knowledge base does not provide sufficient evidence.

---

# 13. Error State

If the backend or model fails:

```text
Something went wrong while generating the response.

Please try again.
```

A retry action should be available:

```text
[Try Again]
```

Technical details should be logged on the backend rather than exposed to the user.

---

# 14. Message Input

The message composer should remain at the bottom of the chat pane.

Example:

```text
┌────────────────────────────────────────────────────────┐
│ Ask a product or growth question...              [➤] │
└────────────────────────────────────────────────────────┘
```

Behavior:

* Enter → submit.
* Shift + Enter → newline.
* Empty message → submission disabled.
* During generation → input may be disabled or allow cancellation.
* Long messages should remain usable without breaking the layout.

---

# 15. New Chat

The `New Chat` button creates a new independent session.

Flow:

```text
Existing Session
       ↓
Click "New Chat"
       ↓
Create new session
       ↓
Clear current messages
       ↓
Display empty state
```

Previous sessions should remain persisted.

---

# 16. Session Handling

The interface may expose a session selector or sidebar.

Example:

```text
Recent Chats

Retention Strategy
Product-Market Fit
Growth Loops
Feature Prioritization
```

Selecting a session loads its persisted conversation.

Each session maintains independent context.

---

# 17. Model Selector

The header should expose the active provider.

Example:

```text
Model: Ollama ▼
```

Options:

```text
Ollama
Claude
```

or:

```text
Ollama
OpenAI
```

depending on the configured cloud provider.

The selected provider should remain visible so the evaluator knows which model is generating the response.

---

# 18. Artifact Viewer

The Artifact Viewer occupies the right side of the desktop layout.

It should have its own header:

```text
Artifact
─────────────────────────────
[Markdown]          [Close]
```

When no artifact exists:

```text
No artifact selected.

Ask the assistant to create a document
or HTML artifact.
```

---

# 19. Markdown Artifact

Markdown artifacts should be rendered as formatted content rather than raw Markdown.

Example:

```text
┌────────────────────────────────────────┐
│ Artifact: Retention Framework          │
├────────────────────────────────────────┤
│                                        │
│ # Retention Framework                  │
│                                        │
│ ## Why Retention Matters               │
│                                        │
│ Strong retention starts with...        │
│                                        │
│ • Identify core value                  │
│ • Measure recurring behavior           │
│ • Remove activation friction           │
│                                        │
└────────────────────────────────────────┘
```

The frontend should use a Markdown renderer such as `react-markdown`.

---

# 20. HTML Artifact

HTML/CSS artifacts should be rendered as an actual preview rather than shown as source code.

Example:

```text
┌────────────────────────────────────────┐
│ Artifact: Growth Dashboard             │
├────────────────────────────────────────┤
│                                        │
│       ┌───────────────────────┐        │
│       │     Dashboard         │        │
│       │                       │        │
│       │  Users     Retention  │        │
│       │  12,430      64%      │        │
│       │                       │        │
│       └───────────────────────┘        │
│                                        │
└────────────────────────────────────────┘
```

Generated HTML is untrusted and therefore must be sanitized and rendered inside a sandboxed iframe.

---

# 21. Artifact Detection

The backend/response processing layer may identify generated artifacts using a structured marker.

Example:

```html
<artifact type="html" title="Growth Dashboard">
...
</artifact>
```

The frontend extracts the artifact and sends it to the appropriate renderer.

Flow:

```text
LLM response
     ↓
Artifact detection
     ↓
Determine type
     │
     ├── markdown → Markdown renderer
     │
     └── html → Sandboxed iframe
```

---

# 22. Artifact Panel States

The Artifact Viewer has four primary states.

### State 1 — Empty

```text
No artifact selected.
```

### State 2 — Loading

```text
Generating artifact...
```

### State 3 — Loaded

```text
Artifact preview
```

### State 4 — Error

```text
Unable to render this artifact.

[Retry]
```

---

# 23. Collapsible Artifact Panel

Desktop:

```text
┌──────────────────┬──────────────────┐
│      Chat        │     Artifact     │
│                  │                  │
│                  │                  │
└──────────────────┴──────────────────┘
```

Collapsed:

```text
┌──────────────────────────────────────┐
│              Chat                    │
│                                      │
│                                      │
└──────────────────────────────────────┘
```

A toggle should allow the user to switch between these states.

The chat should expand to use the available width when the artifact panel is collapsed.

---

# 24. Responsive Design

## Desktop

Use a two-column layout:

```text
Chat: ~60%
Artifact: ~40%
```

The exact ratio can adapt based on available width.

---

## Tablet

Reduce the artifact panel width.

```text
Chat: ~65%
Artifact: ~35%
```

If the screen becomes too narrow, the artifact viewer can become an overlay/drawer.

---

## Mobile

The two-column layout becomes a single-column layout.

Default:

```text
Chat
 ↓
Message Input
```

Artifact becomes a separate expandable view:

```text
[View Artifact]
```

Clicking it opens the artifact viewer.

This prevents the chat interface from becoming unusably narrow.

---

# 25. Accessibility

The application should follow basic accessibility principles.

## Keyboard Navigation

All interactive elements must be keyboard accessible.

Users should be able to:

* Navigate controls.
* Submit messages.
* Open/close artifact viewer.
* Change model provider.

---

## Focus Management

When the artifact panel opens, focus should move appropriately to the panel.

When it closes, focus should return to the triggering control.

---

## Labels

Buttons should have meaningful accessible labels.

Bad:

```text
[ > ]
```

Better:

```text
[ Send message ]
```

---

## Color Contrast

Text and controls should maintain sufficient contrast.

Important information such as errors and status should not rely only on color.

---

## Screen Readers

Important dynamic states should be communicated through appropriate ARIA/live-region behavior.

For example:

```text
Retrieving transcripts...
```

should be announced when appropriate.

---

# 26. Loading States

The application should provide feedback for all potentially slow operations.

### Chat

```text
Retrieving transcripts...
Generating response...
```

### Ship 30

```text
Writing article...
```

### Artifact

```text
Generating artifact...
Rendering preview...
```

### Session

```text
Loading conversation...
```

---

# 27. Interaction State Model

The main chat state can be represented as:

```text
IDLE
 │
 ▼
SUBMITTING
 │
 ▼
RETRIEVING
 │
 ├───────────────┐
 ▼               ▼
SUCCESS        NO_CONTEXT
 │               │
 ▼               ▼
GENERATING     FALLBACK
 │
 ├───────────────┐
 ▼               ▼
COMPLETE        ERROR
```

More specifically:

```text
Idle
 ↓
Request Submitted
 ↓
Retrieving Context
 ↓
Context Found
 ↓
Generating
 ↓
Streaming
 ↓
Complete
```

Failure paths:

```text
Retrieving Context
       ↓
No Relevant Context
       ↓
Insufficient Information
```

or:

```text
Generating
       ↓
Provider Failure
       ↓
Error + Retry
```

---

# 28. Ship 30 for 30 Interaction

The writing feature should be exposed as a clear action after a useful grounded response.

Example:

```text
Assistant response...

Sources
...

[Write as Article]
```

When selected:

```text
Writing a Ship 30 for 30 article...
```

Then the resulting content opens in the Artifact Viewer.

---

# 29. Artifact Interaction

For generated artifacts, the user should be able to:

* Open/close preview.
* Read rendered content.
* Scroll independently from chat.
* Regenerate the artifact.
* Return to the conversation.

Optional future functionality such as downloading or editing artifacts is outside the initial scope.

---

# 30. Error Recovery

Every major failure should have an understandable recovery path.

| Failure                  | UI                       | Recovery                   |
| ------------------------ | ------------------------ | -------------------------- |
| Database unavailable     | Service unavailable      | Retry later                |
| Ollama unavailable       | Model unavailable        | Select cloud provider      |
| Cloud API unavailable    | Provider unavailable     | Try again / local provider |
| No retrieval results     | Insufficient information | Ask another question       |
| Model timeout            | Generation failed        | Retry                      |
| Artifact rendering error | Preview failed           | Retry/regenerate           |

---

# 31. Design Principles

## Principle 1 — Evidence Before Confidence

The UI should make it clear that the assistant's answers come from a knowledge source.

---

## Principle 2 — Don't Hide System State

Users should know whether the system is:

* Searching.
* Generating.
* Finished.
* Failed.

---

## Principle 3 — Keep Technical Complexity Invisible

Users should not need to understand:

* Embeddings.
* pgvector.
* RAG.
* Prompt construction.
* Provider APIs.

Those are implementation details.

---

## Principle 4 — Artifacts Are First-Class Outputs

Generated content should not be treated as raw code dumped into the chat.

The Artifact Viewer should provide a proper preview experience.

---

## Principle 5 — Safe Defaults

The application should default to the safest reasonable behavior:

* Ground answers in retrieved context.
* Reject unsupported questions.
* Sanitize HTML.
* Sandbox generated content.
* Keep secrets server-side.

---

# 32. Visual Hierarchy

The visual hierarchy should follow:

```text
1. User's question
        ↓
2. Assistant answer
        ↓
3. Action / next step
        ↓
4. Sources
        ↓
5. Secondary metadata
```

The answer should remain the most visually important content.

Technical metadata such as provider information should be visible but secondary.

---

# 33. Responsive Behavior Summary

| Screen  | Chat           | Artifact                   |
| ------- | -------------- | -------------------------- |
| Desktop | Primary column | Side panel                 |
| Tablet  | Primary column | Narrow side panel / drawer |
| Mobile  | Full width     | Separate drawer/view       |

---

# 34. Frontend Component Mapping

The design maps to the following components:

```text
components/
│
├── Chat/
│   ├── ChatPane
│   ├── MessageItem
│   ├── MessageInput
│   ├── SourceList
│   ├── SessionSelector
│   └── ModelSelector
│
└── Artifact/
    ├── ArtifactViewer
    ├── MarkdownArtifact
    ├── SandboxedIframe
    └── ArtifactHeader
```

This keeps UI responsibilities separated and makes individual components easier to test.

---

# 35. Final User Experience

The intended experience is:

```text
Open application
       ↓
Immediately understand what it does
       ↓
Ask a product/growth question
       ↓
See retrieval/generation status
       ↓
Watch answer stream into chat
       ↓
See supporting sources
       ↓
Ask follow-up question
       ↓
Generate an article or artifact
       ↓
View artifact beside conversation
```

The interface should feel like a focused professional workspace rather than a generic chatbot.

---

# 36. Design Definition of Done

The design is considered implemented when:

* [ ] Desktop two-column layout works.
* [ ] Chat is the primary interaction.
* [ ] New chat works.
* [ ] Session history can be displayed.
* [ ] User/assistant messages are distinguishable.
* [ ] Streaming state is visible.
* [ ] Retrieval state is visible.
* [ ] Sources are displayed.
* [ ] Insufficient-information state is clear.
* [ ] Error and retry states exist.
* [ ] Model provider is visible.
* [ ] Ship 30 for 30 action is accessible.
* [ ] Artifact viewer opens beside chat.
* [ ] Markdown renders correctly.
* [ ] HTML renders inside a sandbox.
* [ ] Artifact panel can collapse.
* [ ] Mobile layout works.
* [ ] Keyboard navigation works.
* [ ] Important states are accessible.

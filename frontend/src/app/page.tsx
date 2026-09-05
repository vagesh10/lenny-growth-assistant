"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import DOMPurify from "dompurify";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Provider = "ollama" | "openai";

type ArtifactType = "markdown" | "html" | "css";

type Source = {
  episode_title: string;
  guest_name: string | null;
  timestamp: string | null;
  topic: string | null;
  similarity: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

type Artifact = {
  type: ArtifactType;
  content: string;
};

const FALLBACK_ERROR_PREFIX =
  "I do not have sufficient information";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const [provider, setProvider] =
    useState<Provider>("ollama");

  const [artifact, setArtifact] =
    useState<Artifact | null>(null);

  const [artifactType, setArtifactType] =
    useState<ArtifactType>("markdown");

  const [artifactLoading, setArtifactLoading] =
    useState(false);

  const [artifactError, setArtifactError] =
    useState<string | null>(null);

  useEffect(() => {
    createSession();
  }, []);

  async function createSession() {
    try {
      const response = await fetch(
        `${API_URL}/api/sessions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: "New Chat",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to create session");
      }

      const data = await response.json();

      setSessionId(data.id);
    } catch (error) {
      console.error("Session error:", error);
    }
  }

  async function sendMessage() {
    if (
      !message.trim() ||
      !sessionId ||
      loading
    ) {
      return;
    }

    const userMessage = message.trim();

    setMessage("");

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setLoading(true);

    setMessages((previous) => [
      ...previous,
      {
        role: "assistant",
        content: "",
      },
    ]);

    try {
      const response = await fetch(
        `${API_URL}/api/chat/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: userMessage,
            provider,
          }),
        }
      );

      if (!response.ok) {
        let errorMessage =
          "Streaming request failed.";

        try {
          const errorData =
            await response.json();

          if (errorData.detail) {
            errorMessage =
              errorData.detail;
          }
        } catch {
          // Ignore JSON parsing errors.
        }

        throw new Error(errorMessage);
      }

      if (!response.body) {
        throw new Error(
          "Streaming response is unavailable."
        );
      }

      const reader =
        response.body.getReader();

      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { value, done } =
          await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const events =
          buffer.split("\n\n");

        buffer =
          events.pop() || "";

        for (const event of events) {
          if (!event.startsWith("data: ")) {
            continue;
          }

          const data =
            event.replace(
              "data: ",
              ""
            );

          if (data === "[DONE]") {
            continue;
          }

          try {
            const parsed =
              JSON.parse(data);

            if (
              parsed.done &&
              parsed.sources
            ) {
              setMessages((previous) => {
                const updated = [
                  ...previous,
                ];

                const lastMessage =
                  updated[
                    updated.length - 1
                  ];

                if (
                  lastMessage?.role ===
                  "assistant"
                ) {
                  updated[
                    updated.length - 1
                  ] = {
                    ...lastMessage,
                    sources:
                      parsed.sources,
                  };
                }

                return updated;
              });

              continue;
            }

            if (parsed.token) {
              setMessages((previous) => {
                const updated = [
                  ...previous,
                ];

                const lastMessage =
                  updated[
                    updated.length - 1
                  ];

                if (
                  lastMessage?.role ===
                  "assistant"
                ) {
                  updated[
                    updated.length - 1
                  ] = {
                    ...lastMessage,
                    content:
                      lastMessage.content +
                      parsed.token,
                  };
                }

                return updated;
              });
            }
          } catch (error) {
            console.error(
              "Failed to parse SSE event:",
              error
            );
          }
        }
      }
    } catch (error) {
      console.error(
        "Streaming error:",
        error
      );

      const errorMessage =
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again.";

      setMessages((previous) => {
        const updated = [
          ...previous,
        ];

        const lastMessage =
          updated[
            updated.length - 1
          ];

        if (
          lastMessage?.role ===
          "assistant"
        ) {
          updated[
            updated.length - 1
          ] = {
            ...lastMessage,
            content: errorMessage,
          };
        }

        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  async function createArtifact() {
    if (
      !sessionId ||
      artifactLoading ||
      !message.trim()
    ) {
      return;
    }

    const artifactPrompt =
      message.trim();

    setArtifactLoading(true);
    setArtifactError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/artifacts`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            prompt: artifactPrompt,
            artifact_type: artifactType,
            provider,
          }),
        }
      );

      if (!response.ok) {
        let errorMessage =
          "Artifact generation failed.";

        try {
          const errorData =
            await response.json();

          if (errorData.detail) {
            errorMessage =
              errorData.detail;
          }
        } catch {
          // Ignore JSON parsing errors.
        }

        throw new Error(errorMessage);
      }

      const data =
        await response.json();

      if (
        data.content?.startsWith(
          FALLBACK_ERROR_PREFIX
        )
      ) {
        setArtifact(null);
        setArtifactError(
          data.content
        );
        return;
      }

      setArtifact({
        type: data.artifact_type,
        content: data.content,
      });
    } catch (error) {
      console.error(
        "Artifact error:",
        error
      );

      setArtifact(null);

      setArtifactError(
        error instanceof Error
          ? error.message
          : "Something went wrong while generating the artifact."
      );
    } finally {
      setArtifactLoading(false);
    }
  }

  async function generateShip30() {
    if (
      !sessionId ||
      artifactLoading
    ) {
      return;
    }

    setArtifactLoading(true);
    setArtifactError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/artifacts/ship30`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            prompt:
              "Create a Ship 30 plan for improving product onboarding and activation using lessons from Lenny podcast transcripts.",
            artifact_type: "markdown",
            provider,
          }),
        }
      );

      if (!response.ok) {
        let errorMessage =
          "Ship 30 generation failed.";

        try {
          const errorData =
            await response.json();

          if (errorData.detail) {
            errorMessage =
              errorData.detail;
          }
        } catch {
          // Ignore JSON parsing errors.
        }

        throw new Error(errorMessage);
      }

      const data =
        await response.json();

      if (
        data.content?.startsWith(
          FALLBACK_ERROR_PREFIX
        )
      ) {
        setArtifact(null);
        setArtifactError(
          data.content
        );
        return;
      }

      setArtifact({
        type: "markdown",
        content: data.content,
      });

      setArtifactType("markdown");
    } catch (error) {
      console.error(
        "Ship 30 error:",
        error
      );

      setArtifact(null);

      setArtifactError(
        error instanceof Error
          ? error.message
          : "Something went wrong while generating Ship 30."
      );
    } finally {
      setArtifactLoading(false);
    }
  }

  /*
   * Sanitize generated HTML before
   * displaying it inside the iframe.
   *
   * The sandbox provides another
   * isolation layer.
   */
  const sanitizedHtml = useMemo(() => {
    if (
      !artifact ||
      artifact.type !== "html"
    ) {
      return "";
    }

    return DOMPurify.sanitize(
      artifact.content,
      {
        USE_PROFILES: {
          html: true,
        },
        FORBID_TAGS: [
          "script",
          "iframe",
          "object",
          "embed",
          "form",
        ],
      }
    );
  }, [artifact]);

  /*
   * CSS artifacts are wrapped in a
   * complete HTML document so that the
   * generated CSS can be previewed.
   */
  const cssPreviewHtml = useMemo(() => {
    if (
      !artifact ||
      artifact.type !== "css"
    ) {
      return "";
    }

    const escapedCss =
      artifact.content.replace(
        /<\/style/gi,
        "<\\/style"
      );

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8" />

          <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
          />

          <style>
            ${escapedCss}
          </style>
        </head>

        <body>
          <main class="preview">
            <h1>CSS Artifact Preview</h1>

            <p>
              This page demonstrates the generated CSS.
            </p>

            <button>
              Example Button
            </button>

            <div class="card">
              <h2>Example Card</h2>

              <p>
                This is a sample element styled
                by the generated CSS.
              </p>
            </div>
          </main>
        </body>
      </html>
    `;

    return DOMPurify.sanitize(
      html,
      {
        USE_PROFILES: {
          html: true,
        },
        FORBID_TAGS: [
          "script",
          "iframe",
          "object",
          "embed",
          "form",
        ],
      }
    );
  }, [artifact]);

  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}

      <header className="flex h-16 items-center justify-between border-b border-zinc-800 px-6">
        <div>
          <h1 className="text-lg font-semibold">
            Lenny Growth Assistant
          </h1>

          <p className="text-xs text-zinc-500">
            Ask questions about Lenny&apos;s Podcast
          </p>
        </div>

        {/* Model Selector */}

        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">
            Model
          </span>

          <select
            value={provider}
            onChange={(event) =>
              setProvider(
                event.target
                  .value as Provider
              )
            }
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-200 outline-none focus:border-zinc-500"
          >
            <option value="ollama">
              Ollama
            </option>

            <option value="openai">
              OpenAI
            </option>
          </select>
        </div>
      </header>

      {/* Main */}

      <div className="flex h-[calc(100vh-4rem)]">
        {/* Chat */}

        <section className="flex w-1/2 flex-col border-r border-zinc-800">
          <div className="flex-1 overflow-y-auto p-6">
            <div className="mx-auto max-w-2xl">
              {messages.length === 0 ? (
                <div className="mb-8">
                  <p className="mb-2 text-sm text-zinc-500">
                    Lenny Growth Assistant
                  </p>

                  <h2 className="text-2xl font-semibold">
                    What do you want to learn?
                  </h2>

                  <p className="mt-2 text-zinc-400">
                    Ask about product, growth,
                    onboarding, startups,
                    leadership, and more.
                  </p>

                  <div className="mt-6 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={createArtifact}
                      disabled={
                        artifactLoading ||
                        !sessionId ||
                        !message.trim()
                      }
                      className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {artifactLoading
                        ? "Generating artifact..."
                        : "Create Artifact"}
                    </button>

                    <button
                      type="button"
                      onClick={
                        generateShip30
                      }
                      disabled={
                        artifactLoading ||
                        !sessionId
                      }
                      className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 hover:bg-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {artifactLoading
                        ? "Generating Ship 30..."
                        : "🚀 Ship 30"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {messages.map(
                    (item, index) => (
                      <div
                        key={index}
                      >
                        <p className="mb-1 text-xs font-medium uppercase text-zinc-500">
                          {item.role ===
                          "user"
                            ? "You"
                            : "Lenny Assistant"}
                        </p>

                        <div className="rounded-lg bg-zinc-900 p-4 text-sm leading-6 text-zinc-200">
                          <div className="whitespace-pre-wrap">
                            {item.content}
                          </div>

                          {item.role ===
                            "assistant" &&
                            loading &&
                            index ===
                              messages.length -
                                1 && (
                              <span className="ml-1 inline-block animate-pulse">
                                ▌
                              </span>
                            )}

                          {item.role ===
                            "assistant" &&
                            !loading &&
                            item.sources &&
                            item.sources
                              .length >
                              0 && (
                              <div className="mt-5 border-t border-zinc-800 pt-4">
                                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                                  Sources
                                </p>

                                <div className="space-y-2">
                                  {item.sources.map(
                                    (
                                      source,
                                      sourceIndex
                                    ) => (
                                      <div
                                        key={
                                          sourceIndex
                                        }
                                        className="rounded-md border border-zinc-800 bg-zinc-950 p-3"
                                      >
                                        <p className="text-sm font-medium">
                                          {source.guest_name ||
                                            "Unknown Guest"}
                                        </p>

                                        <p className="mt-1 text-xs text-zinc-400">
                                          {
                                            source.episode_title
                                          }
                                        </p>

                                        <div className="mt-2 flex gap-3 text-xs text-zinc-500">
                                          <span>
                                            {source.timestamp ||
                                              "Timestamp unavailable"}
                                          </span>

                                          <span>
                                            Similarity:{" "}
                                            {source.similarity.toFixed(
                                              3
                                            )}
                                          </span>
                                        </div>
                                      </div>
                                    )
                                  )}
                                </div>
                              </div>
                            )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Input */}

          <div className="border-t border-zinc-800 p-4">
            <div className="mx-auto flex max-w-2xl gap-2">
              <input
                type="text"
                value={message}
                onChange={(event) =>
                  setMessage(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key ===
                      "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask Lenny something..."
                disabled={
                  loading ||
                  !sessionId
                }
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm outline-none placeholder:text-zinc-500 focus:border-zinc-500 disabled:opacity-50"
              />

              <button
                type="button"
                onClick={
                  sendMessage
                }
                disabled={
                  loading ||
                  !sessionId ||
                  !message.trim()
                }
                className="rounded-lg bg-white px-5 py-3 text-sm font-medium text-black hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading
                  ? "..."
                  : "Send"}
              </button>

              {/* Artifact Type */}

              <select
                value={artifactType}
                onChange={(event) =>
                  setArtifactType(
                    event.target
                      .value as ArtifactType
                  )
                }
                disabled={
                  loading ||
                  artifactLoading
                }
                className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-3 text-sm text-zinc-200 outline-none focus:border-zinc-500 disabled:opacity-50"
              >
                <option value="markdown">
                  Markdown
                </option>

                <option value="html">
                  HTML
                </option>

                <option value="css">
                  CSS
                </option>
              </select>

              {/* Artifact Button */}

              <button
                type="button"
                onClick={
                  createArtifact
                }
                disabled={
                  loading ||
                  artifactLoading ||
                  !sessionId ||
                  !message.trim()
                }
                className="rounded-lg border border-zinc-700 px-4 py-3 text-sm font-medium text-zinc-200 hover:bg-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {artifactLoading
                  ? "Creating..."
                  : "Artifact"}
              </button>

              {/* Ship 30 */}

              <button
                type="button"
                onClick={
                  generateShip30
                }
                disabled={
                  loading ||
                  artifactLoading ||
                  !sessionId
                }
                className="rounded-lg border border-zinc-700 px-4 py-3 text-sm font-medium text-zinc-200 hover:bg-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {artifactLoading
                  ? "Generating..."
                  : "Ship 30"}
              </button>
            </div>

            <p className="mx-auto mt-2 max-w-2xl text-xs text-zinc-600">
              Press Enter to send
            </p>
          </div>
        </section>

        {/* Artifact */}

        <section className="flex w-1/2 flex-col">
          <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-6">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-medium">
                Artifact Preview
              </h2>

              {artifact && (
                <span className="rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-400">
                  {artifact.type.toUpperCase()}
                </span>
              )}
            </div>

            {artifact && (
              <button
                type="button"
                onClick={() => {
                  setArtifact(
                    null
                  );
                  setArtifactError(
                    null
                  );
                }}
                className="text-xs text-zinc-500 hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-8">
            {artifactError && (
              <div className="mx-auto mb-4 max-w-3xl rounded-lg border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">
                {artifactError}
              </div>
            )}

            {artifact ? (
              <article className="mx-auto max-w-3xl rounded-xl border border-zinc-800 bg-white p-8 text-zinc-900 shadow-xl">
                {/* Markdown */}

                {artifact.type ===
                  "markdown" && (
                  <ReactMarkdown
                    remarkPlugins={[
                      remarkGfm,
                    ]}
                    components={{
                      h1: ({
                        children,
                      }) => (
                        <h1 className="mb-6 text-3xl font-bold">
                          {children}
                        </h1>
                      ),

                      h2: ({
                        children,
                      }) => (
                        <h2 className="mb-4 mt-8 text-xl font-semibold">
                          {children}
                        </h2>
                      ),

                      h3: ({
                        children,
                      }) => (
                        <h3 className="mb-3 mt-6 text-lg font-semibold">
                          {children}
                        </h3>
                      ),

                      p: ({
                        children,
                      }) => (
                        <p className="mb-4 leading-7">
                          {children}
                        </p>
                      ),

                      ul: ({
                        children,
                      }) => (
                        <ul className="mb-4 list-disc space-y-2 pl-6">
                          {children}
                        </ul>
                      ),

                      ol: ({
                        children,
                      }) => (
                        <ol className="mb-4 list-decimal space-y-2 pl-6">
                          {children}
                        </ol>
                      ),

                      li: ({
                        children,
                      }) => (
                        <li>
                          {children}
                        </li>
                      ),

                      strong: ({
                        children,
                      }) => (
                        <strong className="font-semibold">
                          {children}
                        </strong>
                      ),

                      code: ({
                        children,
                      }) => (
                        <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-sm">
                          {children}
                        </code>
                      ),

                      pre: ({
                        children,
                      }) => (
                        <pre className="mb-4 overflow-x-auto rounded-lg bg-zinc-950 p-4 text-sm text-zinc-100">
                          {children}
                        </pre>
                      ),
                    }}
                  >
                    {artifact.content}
                  </ReactMarkdown>
                )}

                {/* HTML */}

                {artifact.type ===
                  "html" && (
                  <iframe
                    title="HTML Artifact Preview"
                    srcDoc={sanitizedHtml}
                    sandbox="allow-scripts"
                    className="min-h-[600px] w-full rounded-lg border border-zinc-200"
                  />
                )}

                {/* CSS */}

                {artifact.type ===
                  "css" && (
                  <iframe
                    title="CSS Artifact Preview"
                    srcDoc={
                      cssPreviewHtml
                    }
                    sandbox="allow-scripts"
                    className="min-h-[600px] w-full rounded-lg border border-zinc-200"
                  />
                )}
              </article>
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg border border-zinc-800 text-xl">
                    ◇
                  </div>

                  <h3 className="text-sm font-medium text-zinc-300">
                    No artifact yet
                  </h3>

                  <p className="mt-1 max-w-xs text-xs leading-5 text-zinc-500">
                    Generated Markdown,
                    HTML, and CSS
                    artifacts will
                    appear here.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
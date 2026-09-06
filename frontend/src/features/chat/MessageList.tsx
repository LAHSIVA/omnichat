import { useEffect, useState } from "react";

import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import {
  getMessages,
  type StreamStatus,
} from "./api";
import type { Message } from "./types";

interface MessageListProps {
  conversationId: string;
  streamingContent?: string;
  isStreaming?: boolean;
  streamStatus?: StreamStatus | null;
  streamStartedAt?: number | null;
}

/* -------------------------------------------------------------------------- */
/* Utilities                                                                  */
/* -------------------------------------------------------------------------- */

function formatElapsedTime(
  milliseconds: number,
): string {
  const totalSeconds = Math.max(
    0,
    Math.floor(milliseconds / 1000),
  );

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${seconds
      .toString()
      .padStart(2, "0")}s`;
  }

  return `${seconds}s`;
}

/* -------------------------------------------------------------------------- */
/* Avatars                                                                    */
/* -------------------------------------------------------------------------- */

function OmniAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-xs font-semibold text-white shadow-sm">
      O
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-[10px] font-semibold text-blue-700">
      You
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Streaming Progress                                                         */
/* -------------------------------------------------------------------------- */

function StreamingProgress({
  status,
  startedAt,
}: {
  status: StreamStatus | null | undefined;
  startedAt: number | null | undefined;
}) {
  const [now, setNow] = useState(() =>
    Date.now(),
  );

  useEffect(() => {
    if (!startedAt) {
      return undefined;
    }

    const interval = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [startedAt]);

  const elapsed = startedAt
    ? now - startedAt
    : 0;

  const stages = [
    {
      key: "preparing",
      label: "Preparing your question",
    },
    {
      key: "retrieving",
      label: "Searching your documents",
    },
    {
      key: "retrieved",
      label: "Checking relevant information",
    },
    {
      key: "building_context",
      label: "Building response context",
    },
    {
      key: "generating",
      label: "Generating answer",
    },
  ] as const;

  const currentStage = status?.stage;

  const currentIndex = stages.findIndex(
    (stage) => stage.key === currentStage,
  );

  const isGeneralMode =
    currentStage === "general";

  return (
    <article className="mb-9">
      <div className="flex gap-3">
        <OmniAvatar />

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900">
              OmniChat
            </span>

            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-medium text-slate-500">
              Working
            </span>
          </div>

          <div className="max-w-3xl rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-blue-600" />

              <span className="text-sm font-medium text-slate-700">
                {status?.message ??
                  "Working on your response..."}
              </span>
            </div>

            <div className="mt-4 space-y-2.5">
              {isGeneralMode ? (
                <div className="flex items-start gap-2.5 text-xs text-slate-500">
                  <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-[9px] font-bold text-emerald-700">
                    ✓
                  </span>

                  <span className="leading-5">
                    No relevant information was found in
                    your documents. Continuing with general
                    knowledge.
                  </span>
                </div>
              ) : (
                stages.map((stage, index) => {
                  const isCurrent =
                    stage.key === currentStage;

                  const isCompleted =
                    currentIndex >= 0 &&
                    index < currentIndex;

                  return (
                    <div
                      key={stage.key}
                      className="flex items-center gap-2.5 text-xs"
                    >
                      <span
                        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${
                          isCompleted
                            ? "bg-emerald-500 text-white"
                            : isCurrent
                              ? "border-2 border-blue-600 bg-white"
                              : "border border-slate-300 bg-white"
                        }`}
                      >
                        {isCompleted && "✓"}

                        {isCurrent && (
                          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-600" />
                        )}
                      </span>

                      <span
                        className={
                          isCurrent
                            ? "font-medium text-slate-800"
                            : isCompleted
                              ? "text-slate-600"
                              : "text-slate-400"
                        }
                      >
                        {stage.label}
                      </span>
                    </div>
                  );
                })
              )}
            </div>

            <div className="mt-4 flex items-center gap-2 border-t border-slate-200 pt-2.5 text-[10px] text-slate-400">
              <span>Elapsed</span>

              <span className="font-medium text-slate-500">
                {formatElapsedTime(elapsed)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

/* -------------------------------------------------------------------------- */
/* User Question                                                              */
/* -------------------------------------------------------------------------- */

function QuestionBlock({
  message,
}: {
  message: Message;
}) {
  return (
    <article className="mb-8">
      <div className="flex gap-3">
        <UserAvatar />

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-800">
              Your question
            </span>
          </div>

          <div className="max-w-3xl rounded-2xl border border-blue-100 bg-blue-50/70 px-4 py-3.5 shadow-sm">
            <div className="prose prose-sm max-w-none text-slate-800 prose-p:my-0 prose-headings:text-slate-900 prose-strong:text-slate-900">
              <ReactMarkdown>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

/* -------------------------------------------------------------------------- */
/* Sources                                                                    */
/* -------------------------------------------------------------------------- */

function SourceSection({
  sources,
}: {
  sources: NonNullable<Message["sources"]>;
}) {
  if (!sources.length) {
    return null;
  }

  return (
    <div className="mt-6 border-t border-slate-200/80 pt-4">
      <div className="mb-3 flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="h-3.5 w-3.5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 4h9l3 3v13H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z"
            />

            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M14 4v4h4"
            />
          </svg>
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-700">
            Sources
          </p>

          <p className="text-[10px] text-slate-400">
            Information used to ground this answer
          </p>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {sources.map((source, index) => (
          <div
            key={`${source.document_id}-${index}`}
            className="group flex min-w-0 items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm transition hover:border-blue-200 hover:bg-blue-50/30"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-slate-500 ring-1 ring-slate-200">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-3.5 w-3.5"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                />

                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M14 3v5h5"
                />
              </svg>
            </div>

            <div className="min-w-0 flex-1">
              <p
                className="truncate text-xs font-semibold text-slate-700 group-hover:text-slate-900"
                title={
                  source.document_title ??
                  source.original_filename ??
                  "Document"
                }
              >
                {source.document_title ??
                  source.original_filename ??
                  "Document"}
              </p>

              <p className="mt-0.5 text-[10px] text-slate-400">
                Supporting document
              </p>
            </div>

            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-3.5 w-3.5 shrink-0 text-slate-300 transition group-hover:text-blue-500"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m9 18 6-6-6-6"
              />
            </svg>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* AI Answer                                                                  */
/* -------------------------------------------------------------------------- */

function AnswerBlock({
  message,
}: {
  message: Message;
}) {
  const hasSources =
    Boolean(
      message.sources &&
        message.sources.length > 0,
    );

  return (
    <article className="mb-10">
      <div className="flex gap-3">
        <OmniAvatar />

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900">
              OmniChat
            </span>

            {hasSources && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-semibold text-emerald-700 ring-1 ring-emerald-100">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Grounded
              </span>
            )}
          </div>

          <div
            className={`max-w-3xl rounded-2xl border px-5 py-4 shadow-sm ${
              hasSources
                ? "border-emerald-100 bg-gradient-to-br from-white via-white to-emerald-50/40"
                : "border-slate-200 bg-white"
            }`}
          >
            <div className="prose prose-sm max-w-none leading-7 text-slate-700 prose-headings:font-semibold prose-headings:tracking-tight prose-headings:text-slate-950 prose-h1:mb-4 prose-h1:mt-0 prose-h1:text-2xl prose-h2:mb-3 prose-h2:mt-7 prose-h2:text-lg prose-h3:mb-2 prose-h3:mt-6 prose-h3:text-base prose-p:my-3 prose-strong:font-semibold prose-strong:text-slate-950 prose-a:font-medium prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-li:my-1.5 prose-ul:my-3 prose-ol:my-3 prose-code:rounded-md prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-[12px] prose-code:font-medium prose-code:text-slate-700 prose-pre:my-4 prose-pre:overflow-x-auto prose-pre:rounded-xl prose-pre:border prose-pre:border-slate-200 prose-pre:bg-slate-950 prose-pre:text-slate-100 prose-blockquote:my-4 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50/60 prose-blockquote:px-4 prose-blockquote:py-2 prose-blockquote:text-slate-600">
              <ReactMarkdown>
                {message.content}
              </ReactMarkdown>
            </div>

            {hasSources && (
              <SourceSection
                sources={message.sources ?? []}
              />
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

/* -------------------------------------------------------------------------- */
/* Streaming Answer                                                           */
/* -------------------------------------------------------------------------- */

function StreamingAnswer({
  content,
}: {
  content: string;
}) {
  return (
    <article className="mb-10">
      <div className="flex gap-3">
        <OmniAvatar />

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900">
              OmniChat
            </span>

            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[9px] font-semibold text-blue-700">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
              Generating
            </span>
          </div>

          <div className="max-w-3xl rounded-2xl border border-blue-100 bg-gradient-to-br from-white via-white to-blue-50/30 px-5 py-4 shadow-sm">
            <div className="prose prose-sm max-w-none leading-7 text-slate-700 prose-headings:font-semibold prose-headings:tracking-tight prose-headings:text-slate-950 prose-h1:mb-4 prose-h1:mt-0 prose-h1:text-2xl prose-h2:mb-3 prose-h2:mt-7 prose-h2:text-lg prose-h3:mb-2 prose-h3:mt-6 prose-h3:text-base prose-p:my-3 prose-strong:font-semibold prose-strong:text-slate-950 prose-li:my-1.5 prose-ul:my-3 prose-ol:my-3 prose-code:rounded-md prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-[12px] prose-code:font-medium prose-code:text-slate-700 prose-pre:my-4 prose-pre:overflow-x-auto prose-pre:rounded-xl prose-pre:border prose-pre:border-slate-200 prose-pre:bg-slate-950 prose-pre:text-slate-100 prose-blockquote:my-4 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50/60 prose-blockquote:px-4 prose-blockquote:py-2 prose-blockquote:text-slate-600">
              <ReactMarkdown>
                {content}
              </ReactMarkdown>
            </div>

            <span className="ml-1 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-blue-600 align-middle" />
          </div>
        </div>
      </div>
    </article>
  );
}

/* -------------------------------------------------------------------------- */
/* Main Message List                                                          */
/* -------------------------------------------------------------------------- */

function MessageList({
  conversationId,
  streamingContent = "",
  isStreaming = false,
  streamStatus = null,
  streamStartedAt = null,
}: MessageListProps) {
  const {
    data: messages,
    isLoading,
    isError,
  } = useQuery<Message[]>({
    queryKey: ["messages", conversationId],
    queryFn: () => getMessages(conversationId),
    enabled: Boolean(conversationId),
  });

  /* ------------------------------------------------------------------------ */
  /* Loading                                                                  */
  /* ------------------------------------------------------------------------ */

  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto bg-white px-5 py-8 sm:px-8">
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="flex gap-3">
            <div className="h-8 w-8 shrink-0 animate-pulse rounded-xl bg-slate-200" />

            <div className="h-14 w-64 animate-pulse rounded-2xl bg-blue-50" />
          </div>

          <div className="flex gap-3">
            <div className="h-8 w-8 shrink-0 animate-pulse rounded-xl bg-slate-200" />

            <div className="h-32 w-full max-w-3xl animate-pulse rounded-2xl bg-slate-100" />
          </div>
        </div>
      </div>
    );
  }

  /* ------------------------------------------------------------------------ */
  /* Error                                                                    */
  /* ------------------------------------------------------------------------ */

  if (isError) {
    return (
      <div className="flex h-full items-center justify-center bg-white px-6">
        <div className="max-w-sm rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-center shadow-sm">
          <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-600">
            !
          </div>

          <p className="text-sm font-semibold text-red-700">
            Unable to load messages
          </p>

          <p className="mt-1 text-xs leading-5 text-red-600">
            Please try refreshing the conversation.
          </p>
        </div>
      </div>
    );
  }

  const hasMessages =
    Boolean(messages && messages.length > 0);

  const hasStreamingContent =
    Boolean(streamingContent);

  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8 lg:px-10">
        {/* ---------------------------------------------------------------- */}
        {/* Empty conversation                                               */}
        {/* ---------------------------------------------------------------- */}

        {!hasMessages && !isStreaming && (
          <div className="flex min-h-[60vh] items-center justify-center">
            <div className="w-full max-w-lg text-center">
              <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-sm">
                <span className="text-lg font-semibold">
                  O
                </span>
              </div>

              <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                What would you like to learn?
              </h2>

              <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-500">
                Ask a question, explore a concept, or
                upload your documents and let OmniChat
                help you understand them.
              </p>

              <div className="mx-auto mt-7 grid max-w-md gap-2 text-left sm:grid-cols-2">
                <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-3.5">
                  <p className="text-xs font-semibold text-slate-800">
                    Understand
                  </p>

                  <p className="mt-1 text-[11px] leading-4 text-slate-500">
                    Break difficult concepts into simple
                    explanations.
                  </p>
                </div>

                <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-3.5">
                  <p className="text-xs font-semibold text-slate-800">
                    Study
                  </p>

                  <p className="mt-1 text-[11px] leading-4 text-slate-500">
                    Turn your documents into a useful
                    learning companion.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Messages                                                          */}
        {/* ---------------------------------------------------------------- */}

        {messages?.map((message) =>
          message.role === "user" ? (
            <QuestionBlock
              key={message.id}
              message={message}
            />
          ) : (
            <AnswerBlock
              key={message.id}
              message={message}
            />
          ),
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Streaming                                                          */}
        {/* ---------------------------------------------------------------- */}

        {isStreaming && !hasStreamingContent && (
          <StreamingProgress
            status={streamStatus}
            startedAt={streamStartedAt}
          />
        )}

        {isStreaming && hasStreamingContent && (
          <StreamingAnswer
            content={streamingContent}
          />
        )}

        <div className="h-8" />
      </div>
    </div>
  );
}

export default MessageList;

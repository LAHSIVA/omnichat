import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import ChatInput from "../features/chat/ChatInput";
import ConversationSidebar from "../features/chat/ConversationSidebar";
import MessageList from "../features/chat/MessageList";
import {
  createConversation,
  type StreamStatus,
} from "../features/chat/api";

const SELECTED_CONVERSATION_KEY =
  "omnichat_selected_conversation";

function ChatPage() {
  const queryClient = useQueryClient();

  const [selectedConversationId, setSelectedConversationId] =
    useState<string | null>(() =>
      localStorage.getItem(
        SELECTED_CONVERSATION_KEY,
      ),
    );

  const [streamingContent, setStreamingContent] =
    useState("");

  const [streamStatus, setStreamStatus] =
    useState<StreamStatus | null>(null);

  const [streamStartedAt, setStreamStartedAt] =
    useState<number | null>(null);

  const [isStreaming, setIsStreaming] =
    useState(false);

  /* ------------------------------------------------------------------------ */
  /* Persist selected conversation                                            */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (selectedConversationId) {
      localStorage.setItem(
        SELECTED_CONVERSATION_KEY,
        selectedConversationId,
      );
    } else {
      localStorage.removeItem(
        SELECTED_CONVERSATION_KEY,
      );
    }
  }, [selectedConversationId]);

  /* ------------------------------------------------------------------------ */
  /* New conversation                                                         */
  /* ------------------------------------------------------------------------ */

  async function handleNewConversation() {
    try {
      const conversation =
        await createConversation();

      setSelectedConversationId(
        conversation.id,
      );

      setStreamingContent("");
      setStreamStatus(null);
      setStreamStartedAt(null);
      setIsStreaming(false);

      await queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });
    } catch (error) {
      console.error(
        "Failed to create conversation:",
        error,
      );
    }
  }

  /* ------------------------------------------------------------------------ */
  /* Streaming lifecycle                                                      */
  /* ------------------------------------------------------------------------ */

  function handleStreamStart() {
    setStreamingContent("");

    setStreamStatus({
      stage: "preparing",
      message: "Preparing your question...",
    });

    setStreamStartedAt(Date.now());
    setIsStreaming(true);
  }

  function handleStreamStatus(
    status: StreamStatus,
  ) {
    setStreamStatus(status);
  }

  function handleStreamToken(
    token: string,
  ) {
    setStreamingContent(
      (current) => current + token,
    );
  }

  async function handleMessageSent() {
    setIsStreaming(false);
    setStreamStatus(null);
    setStreamStartedAt(null);

    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: [
          "messages",
          selectedConversationId,
        ],
      }),
      queryClient.invalidateQueries({
        queryKey: ["conversations"],
      }),
    ]);
  }

  function handleStreamError() {
    setIsStreaming(false);
    setStreamStatus(null);
    setStreamStartedAt(null);
    setStreamingContent("");

    void queryClient.invalidateQueries({
      queryKey: [
        "messages",
        selectedConversationId,
      ],
    });
  }

  /* ------------------------------------------------------------------------ */
  /* Conversation selection                                                   */
  /* ------------------------------------------------------------------------ */

  function handleConversationSelect(
    conversationId: string,
  ) {
    if (isStreaming) {
      return;
    }

    setSelectedConversationId(
      conversationId,
    );

    setStreamingContent("");
    setStreamStatus(null);
    setStreamStartedAt(null);
  }

  /* ------------------------------------------------------------------------ */
  /* Header status                                                             */
  /* ------------------------------------------------------------------------ */

  const headerStatus =
    isStreaming
      ? streamStatus?.message ??
        "Working on your response..."
      : "Ready";

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-slate-50 text-slate-900">
      {/* ================================================================== */}
      {/* SIDEBAR                                                             */}
      {/* ================================================================== */}

      <aside className="flex w-[300px] shrink-0 flex-col border-r border-slate-200 bg-slate-50">
        <ConversationSidebar
          selectedConversationId={
            selectedConversationId
          }
          onSelectConversation={
            handleConversationSelect
          }
        />
      </aside>

      {/* ================================================================== */}
      {/* MAIN WORKSPACE                                                      */}
      {/* ================================================================== */}

      <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
        {/* ---------------------------------------------------------------- */}
        {/* Very subtle background atmosphere                                */}
        {/* ---------------------------------------------------------------- */}

        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 overflow-hidden"
        >
          <div className="absolute -right-40 top-0 h-[420px] w-[420px] rounded-full bg-blue-50/50 blur-3xl" />

          <div className="absolute -left-40 bottom-20 h-[360px] w-[360px] rounded-full bg-slate-100/70 blur-3xl" />

          <div className="absolute left-1/2 top-1/3 h-[260px] w-[260px] -translate-x-1/2 rounded-full bg-emerald-50/30 blur-3xl" />
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Header                                                             */}
        {/* ---------------------------------------------------------------- */}

        <header className="relative z-10 flex h-[64px] shrink-0 items-center border-b border-slate-200/90 bg-white/90 px-5 backdrop-blur-md sm:px-7">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            {/* OmniChat mark */}
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-xs font-semibold text-white shadow-sm">
              O
            </div>

            {/* Title */}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="truncate text-sm font-semibold tracking-tight text-slate-950">
                  OmniChat
                </h1>

                {selectedConversationId && (
                  <span className="hidden text-slate-300 sm:inline">
                    /
                  </span>
                )}

                {selectedConversationId && (
                  <span className="hidden max-w-[220px] truncate text-xs text-slate-400 md:block">
                    Conversation
                  </span>
                )}
              </div>

              <div className="mt-0.5 flex items-center gap-1.5">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    isStreaming
                      ? "animate-pulse bg-blue-500"
                      : "bg-emerald-500"
                  }`}
                />

                <span className="max-w-[300px] truncate text-[10px] text-slate-400">
                  {headerStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Right-side workspace indicators */}
          <div className="flex shrink-0 items-center gap-2">
            {isStreaming && (
              <div className="hidden items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 sm:flex">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />

                <span className="text-[10px] font-medium text-blue-700">
                  AI working
                </span>
              </div>
            )}

            {!isStreaming && (
              <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 sm:flex">
                <span className="text-[10px] font-medium text-slate-500">
                  AI Workspace
                </span>
              </div>
            )}
          </div>
        </header>

        {/* ---------------------------------------------------------------- */}
        {/* Conversation content                                              */}
        {/* ---------------------------------------------------------------- */}

        <div className="relative z-0 min-h-0 flex-1">
          {selectedConversationId ? (
            <MessageList
              conversationId={
                selectedConversationId
              }
              streamingContent={
                streamingContent
              }
              isStreaming={isStreaming}
              streamStatus={streamStatus}
              streamStartedAt={
                streamStartedAt
              }
            />
          ) : (
            <div className="relative flex h-full items-center justify-center overflow-y-auto px-6">
              <div className="w-full max-w-xl text-center">
                {/* Welcome icon */}
                <div className="mx-auto mb-6 flex h-[68px] w-[68px] items-center justify-center rounded-[20px] border border-slate-200 bg-white shadow-[0_10px_35px_rgba(15,23,42,0.08)]">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-base font-semibold text-white shadow-sm">
                    O
                  </div>
                </div>

                {/* Heading */}
                <h2 className="text-3xl font-semibold tracking-[-0.025em] text-slate-950 sm:text-[34px]">
                  What would you like to learn?
                </h2>

                <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-500">
                  Ask questions, understand difficult
                  concepts, or explore your uploaded
                  documents with grounded AI.
                </p>

                {/* Quick-start cards */}
                <div className="mx-auto mt-8 grid max-w-lg gap-3 text-left sm:grid-cols-3">
                  <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-4 transition hover:border-blue-200 hover:bg-blue-50">
                    <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        className="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M9 18h6M10 22h4M8.5 14.5a7 7 0 1 1 7 0c-.9.7-1.5 1.4-1.5 2.5h-4c0-1.1-.6-1.8-1.5-2.5Z"
                        />
                      </svg>
                    </div>

                    <p className="text-xs font-semibold text-slate-800">
                      Understand
                    </p>

                    <p className="mt-1 text-[11px] leading-4 text-slate-500">
                      Break complex topics into clear
                      explanations.
                    </p>
                  </div>

                  <div className="rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4 transition hover:border-emerald-200 hover:bg-emerald-50/70">
                    <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        className="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"
                        />
                      </svg>
                    </div>

                    <p className="text-xs font-semibold text-slate-800">
                      Study
                    </p>

                    <p className="mt-1 text-[11px] leading-4 text-slate-500">
                      Turn your documents into a learning
                      companion.
                    </p>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition hover:border-slate-300 hover:bg-slate-100">
                    <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-slate-200 text-slate-600">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        className="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 3v18M3 12h18"
                        />
                      </svg>
                    </div>

                    <p className="text-xs font-semibold text-slate-800">
                      Explore
                    </p>

                    <p className="mt-1 text-[11px] leading-4 text-slate-500">
                      Ask follow-up questions and go deeper.
                    </p>
                  </div>
                </div>

                {/* CTA */}
                <button
                  type="button"
                  onClick={
                    handleNewConversation
                  }
                  className="mt-8 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800 hover:shadow-md focus:outline-none focus:ring-4 focus:ring-blue-500/10 active:scale-[0.98]"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="h-4 w-4"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 5v14M5 12h14"
                    />
                  </svg>

                  Start a new chat
                </button>

                <p className="mt-4 text-[10px] text-slate-400">
                  Your uploaded documents can be used as
                  trusted knowledge sources.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Composer                                                          */}
        {/* ---------------------------------------------------------------- */}

        {selectedConversationId && (
          <div className="relative z-10 shrink-0 border-t border-slate-200/80 bg-white/90 px-4 pb-3 pt-3 backdrop-blur-md sm:px-7 sm:pb-4">
            <div className="mx-auto max-w-4xl">
              <ChatInput
                conversationId={
                  selectedConversationId
                }
                onStreamStart={
                  handleStreamStart
                }
                onStatus={
                  handleStreamStatus
                }
                onToken={
                  handleStreamToken
                }
                onMessageSent={
                  handleMessageSent
                }
                onStreamError={
                  handleStreamError
                }
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default ChatPage;

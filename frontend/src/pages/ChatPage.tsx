import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import ConversationSidebar from "../features/chat/ConversationSidebar";
import MessageList from "../features/chat/MessageList";
import ChatInput from "../features/chat/ChatInput";
import DocumentPanel from "../features/documents/DocumentPanel";

function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] =
    useState<string | null>(() => {
      return localStorage.getItem("omnichat_selected_conversation");
    });

  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const queryClient = useQueryClient();

  useEffect(() => {
    if (selectedConversationId) {
      localStorage.setItem(
        "omnichat_selected_conversation",
        selectedConversationId,
      );
    } else {
      localStorage.removeItem("omnichat_selected_conversation");
    }
  }, [selectedConversationId]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsSidebarOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  function handleStreamStart() {
    setStreamingContent("");
    setIsStreaming(true);

    if (!selectedConversationId) {
      return;
    }

    queryClient.invalidateQueries({
      queryKey: ["messages", selectedConversationId],
    });
  }

  function handleStreamToken(token: string) {
    setStreamingContent((currentContent) => currentContent + token);
  }

  function handleMessageSent() {
    if (!selectedConversationId) {
      return;
    }

    setIsStreaming(false);
    setStreamingContent("");

    queryClient.invalidateQueries({
      queryKey: ["messages", selectedConversationId],
    });

    queryClient.invalidateQueries({
      queryKey: ["conversations"],
    });
  }

  function handleStreamError() {
    setIsStreaming(false);
    setStreamingContent("");

    if (!selectedConversationId) {
      return;
    }

    queryClient.invalidateQueries({
      queryKey: ["messages", selectedConversationId],
    });
  }

  function handleConversationSelect(conversationId: string) {
    setSelectedConversationId(conversationId);
    setStreamingContent("");
    setIsStreaming(false);
    setIsSidebarOpen(false);
  }

  function handleOpenSidebar() {
    setIsSidebarOpen(true);
  }

  function handleCloseSidebar() {
    setIsSidebarOpen(false);
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-slate-900">
      {/* Desktop sidebar */}
      <aside className="hidden h-screen w-[280px] min-w-[280px] shrink-0 flex-col overflow-hidden border-r border-slate-200 bg-[#f7f7f8] lg:flex">
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ConversationSidebar
            selectedConversationId={selectedConversationId}
            onSelectConversation={handleConversationSelect}
          />
        </div>

        <div className="shrink-0 border-t border-slate-200 bg-[#f7f7f8]">
          <DocumentPanel />
        </div>
      </aside>

      {/* Mobile / tablet sidebar drawer */}
      <div
        className={`fixed inset-0 z-50 lg:hidden ${
          isSidebarOpen ? "pointer-events-auto" : "pointer-events-none"
        }`}
        aria-hidden={!isSidebarOpen}
      >
        {/* Backdrop */}
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={handleCloseSidebar}
          className={`absolute inset-0 bg-slate-950/30 backdrop-blur-[1px] transition-opacity duration-200 ${
            isSidebarOpen ? "opacity-100" : "opacity-0"
          }`}
        />

        {/* Drawer */}
        <aside
          className={`relative flex h-full w-[min(86vw,320px)] flex-col overflow-hidden border-r border-slate-200 bg-[#f7f7f8] shadow-2xl transition-transform duration-200 ease-out ${
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
          aria-label="Conversation sidebar"
        >
          <div className="min-h-0 flex-1 overflow-y-auto">
            <ConversationSidebar
              selectedConversationId={selectedConversationId}
              onSelectConversation={handleConversationSelect}
            />
          </div>

          <div className="shrink-0 border-t border-slate-200 bg-[#f7f7f8]">
            <DocumentPanel />
          </div>
        </aside>
      </div>

      {/* Main workspace */}
      <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
        {selectedConversationId ? (
          <>
            {/* Workspace header */}
            <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-100 bg-white px-4 sm:px-6 lg:px-8">
              <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
                {/* Mobile menu button */}
                <button
                  type="button"
                  aria-label="Open sidebar"
                  aria-expanded={isSidebarOpen}
                  onClick={handleOpenSidebar}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 lg:hidden"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-5 w-5"
                    aria-hidden="true"
                  >
                    <path d="M4 6h16" />
                    <path d="M4 12h16" />
                    <path d="M4 18h16" />
                  </svg>
                </button>

                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white">
                  O
                </div>

                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-900">
                    OmniChat
                  </p>

                  <div className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    <span className="text-xs text-slate-400">
                      AI workspace
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-500 sm:px-3">
                  {isStreaming ? "Generating..." : "Ready"}
                </span>
              </div>
            </header>

            {/* Messages */}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="mx-auto min-h-full w-full max-w-4xl px-4 pb-36 pt-5 sm:px-6 sm:pb-36 sm:pt-8">
                <MessageList
                  conversationId={selectedConversationId}
                  streamingContent={streamingContent}
                  isStreaming={isStreaming}
                />
              </div>
            </div>

            {/* Composer */}
            <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10">
              <div className="pointer-events-auto mx-auto w-full max-w-4xl px-3 pb-3 sm:px-6 sm:pb-6">
                <ChatInput
                  conversationId={selectedConversationId}
                  onStreamStart={handleStreamStart}
                  onToken={handleStreamToken}
                  onMessageSent={handleMessageSent}
                  onStreamError={handleStreamError}
                />
              </div>
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex min-h-0 flex-1 items-center justify-center overflow-y-auto px-5 py-10">
            <div className="w-full max-w-2xl">
              <div className="text-center">
                {/* Mobile menu button */}
                <div className="mb-6 flex items-center justify-center lg:hidden">
                  <button
                    type="button"
                    aria-label="Open sidebar"
                    onClick={handleOpenSidebar}
                    className="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4"
                      aria-hidden="true"
                    >
                      <path d="M4 6h16" />
                      <path d="M4 12h16" />
                      <path d="M4 18h16" />
                    </svg>
                    <span>Conversations</span>
                  </button>
                </div>

                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-950 text-xl font-bold text-white shadow-lg shadow-slate-950/10">
                  O
                </div>

                <p className="mb-3 text-sm font-medium uppercase tracking-[0.16em] text-slate-400">
                  AI Workspace
                </p>

                <h1 className="text-3xl font-semibold tracking-[-0.03em] text-slate-950 sm:text-4xl">
                  Welcome to OmniChat
                </h1>

                <p className="mx-auto mt-4 max-w-lg text-sm leading-6 text-slate-500 sm:text-base">
                  Have a conversation with AI, or bring your own documents
                  and ask questions grounded in your knowledge.
                </p>
              </div>

              <div className="mt-10 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
                  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-sm font-semibold text-slate-700">
                    AI
                  </div>

                  <h2 className="text-sm font-semibold text-slate-900">
                    Ask anything
                  </h2>

                  <p className="mt-1.5 text-xs leading-5 text-slate-500">
                    Explore ideas, solve problems, and work through
                    complex questions.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
                  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-sm font-semibold text-slate-700">
                    RAG
                  </div>

                  <h2 className="text-sm font-semibold text-slate-900">
                    Ask your documents
                  </h2>

                  <p className="mt-1.5 text-xs leading-5 text-slate-500">
                    Upload documents and get answers based on their
                    contents.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
                  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-sm font-semibold text-slate-700">
                    ↗
                  </div>

                  <h2 className="text-sm font-semibold text-slate-900">
                    Keep context
                  </h2>

                  <p className="mt-1.5 text-xs leading-5 text-slate-500">
                    Continue conversations without losing your previous
                    messages.
                  </p>
                </div>
              </div>

              <div className="mt-8 flex justify-center">
                <p className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-center text-xs text-slate-400">
                  Select a conversation from the sidebar to begin
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default ChatPage;
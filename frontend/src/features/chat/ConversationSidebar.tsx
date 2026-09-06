import { useCallback, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createConversation,
  deleteConversation,
  getConversations,
} from "./api";

import { useAuth } from "../auth/useAuth";
import DocumentPanel from "../documents/DocumentPanel";

interface ConversationSidebarProps {
  selectedConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
}

function ConversationSidebar({
  selectedConversationId,
  onSelectConversation,
}: ConversationSidebarProps) {
  const queryClient = useQueryClient();
  const { user, logout } = useAuth();

  const [isCreating, setIsCreating] = useState(false);
  const [deletingConversationId, setDeletingConversationId] =
    useState<string | null>(null);

  const {
    data: conversations = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["conversations"],
    queryFn: getConversations,
  });

  const handleNewChat = useCallback(async () => {
    if (isCreating) {
      return;
    }

    setIsCreating(true);

    try {
      const conversation = await createConversation();

      await queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });

      onSelectConversation(conversation.id);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    } finally {
      setIsCreating(false);
    }
  }, [isCreating, onSelectConversation, queryClient]);

  async function handleDelete(
    event: React.MouseEvent,
    conversationId: string,
  ) {
    event.stopPropagation();

    if (deletingConversationId) {
      return;
    }

    const conversation = conversations.find(
      (item) => item.id === conversationId,
    );

    const conversationTitle =
      conversation?.title || "this conversation";

    const confirmed = window.confirm(
      `Delete "${conversationTitle}"?\n\nThis action cannot be undone.`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingConversationId(conversationId);

    try {
      await deleteConversation(conversationId);

      await queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });

      if (conversationId === selectedConversationId) {
        onSelectConversation("");
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    } finally {
      setDeletingConversationId(null);
    }
  }

  useEffect(() => {
    function handleKeyboardShortcut(event: KeyboardEvent) {
      const isShortcut =
        (event.ctrlKey || event.metaKey) &&
        event.key.toLowerCase() === "k";

      if (!isShortcut) {
        return;
      }

      event.preventDefault();

      void handleNewChat();
    }

    window.addEventListener("keydown", handleKeyboardShortcut);

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyboardShortcut,
      );
    };
  }, [handleNewChat]);

  const usernameInitial =
    user?.username?.charAt(0).toUpperCase() || "U";

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-slate-50">
      {/* ─────────────────────────────────────────
          BRAND
      ───────────────────────────────────────── */}
      <div className="shrink-0 px-5 pb-4 pt-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white shadow-sm">
            O
          </div>

          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold tracking-tight text-slate-900">
              OmniChat
            </h1>

            <p className="text-[10px] font-medium uppercase tracking-[0.08em] text-slate-400">
              AI Workspace
            </p>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────
          NEW CHAT
      ───────────────────────────────────────── */}
      <div className="shrink-0 px-4">
        <button
          type="button"
          onClick={() => void handleNewChat()}
          disabled={isCreating}
          className="group flex h-10 w-full items-center gap-3 rounded-xl bg-slate-900 px-3.5 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-blue-500/10 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
        >
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-white/10 text-sm font-medium leading-none text-white">
            {isCreating ? (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                className="h-3.5 w-3.5 animate-spin"
                aria-hidden="true"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="9"
                  stroke="currentColor"
                  strokeWidth="3"
                  className="opacity-30"
                />
                <path
                  d="M21 12a9 9 0 0 0-9-9"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            ) : (
              "+"
            )}
          </span>

          <span>
            {isCreating ? "Creating..." : "New chat"}
          </span>

          {!isCreating && (
            <span className="ml-auto rounded-md bg-white/10 px-1.5 py-0.5 text-[9px] font-medium text-slate-300">
              Ctrl K
            </span>
          )}
        </button>
      </div>

      {/* ─────────────────────────────────────────
          SCROLLABLE WORKSPACE
      ───────────────────────────────────────── */}
      <div className="min-h-0 flex-1 overflow-y-auto px-1 py-6">
        {/* Conversations */}
        <section>
          <div className="mb-2 flex items-center justify-between px-4">
            <h2 className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
              Conversations
            </h2>

            {!isLoading &&
              !isError &&
              conversations.length > 0 && (
                <span className="rounded-md bg-slate-200/70 px-1.5 py-0.5 text-[9px] font-semibold text-slate-500">
                  {conversations.length}
                </span>
              )}
          </div>

          {/* Loading */}
          {isLoading && (
            <div className="space-y-1.5 px-3">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="h-9 animate-pulse rounded-xl bg-slate-200/60"
                />
              ))}
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="mx-3 rounded-xl border border-red-200 bg-red-50 p-3">
              <div className="flex items-start gap-2">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-xs font-bold text-red-600">
                  !
                </span>

                <div className="min-w-0">
                  <p className="text-xs font-medium text-red-700">
                    Unable to load chats
                  </p>

                  <button
                    type="button"
                    onClick={() => void refetch()}
                    className="mt-1.5 text-[10px] font-semibold text-red-700 underline underline-offset-2 hover:text-red-800"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Empty */}
          {!isLoading &&
            !isError &&
            conversations.length === 0 && (
              <div className="px-6 py-6 text-center">
                <div className="mx-auto mb-2 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-200/70 text-slate-400">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    className="h-4 w-4"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8 10h8M8 14h5m7-2a8 8 0 0 1-8 8 8.3 8.3 0 0 1-3.7-.86L4 20l.86-4.3A8.3 8.3 0 1 1 20 12Z"
                    />
                  </svg>
                </div>

                <p className="text-[11px] font-medium text-slate-600">
                  No conversations yet
                </p>

                <p className="mt-1 text-[10px] leading-4 text-slate-400">
                  Start a new chat to begin.
                </p>
              </div>
            )}

          {/* Conversation list */}
          {!isLoading &&
            !isError &&
            conversations.length > 0 && (
              <div className="space-y-0.5 px-2">
                {conversations.map((conversation) => {
                  const isSelected =
                    conversation.id ===
                    selectedConversationId;

                  const isDeleting =
                    conversation.id ===
                    deletingConversationId;

                  return (
                    <div
                      key={conversation.id}
                      className={`group flex min-w-0 items-center rounded-xl transition ${
                        isSelected
                          ? "bg-blue-50 ring-1 ring-blue-100"
                          : "hover:bg-slate-200/60"
                      } ${
                        isDeleting ? "opacity-60" : ""
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() =>
                          onSelectConversation(
                            conversation.id,
                          )
                        }
                        disabled={isDeleting}
                        title={
                          conversation.title ||
                          "New conversation"
                        }
                        className="flex min-w-0 flex-1 items-center gap-2.5 px-3 py-2.5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 focus-visible:ring-inset disabled:cursor-not-allowed"
                      >
                        <span
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                            isSelected
                              ? "bg-blue-600 text-white"
                              : "bg-slate-200 text-slate-500 group-hover:bg-slate-300"
                          }`}
                        >
                          {isDeleting ? (
                            <svg
                              viewBox="0 0 24 24"
                              fill="none"
                              className="h-3.5 w-3.5 animate-spin"
                            >
                              <circle
                                cx="12"
                                cy="12"
                                r="9"
                                stroke="currentColor"
                                strokeWidth="3"
                                className="opacity-25"
                              />
                              <path
                                d="M21 12a9 9 0 0 0-9-9"
                                stroke="currentColor"
                                strokeWidth="3"
                                strokeLinecap="round"
                              />
                            </svg>
                          ) : (
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
                                d="M8 10h8M8 14h5m7-2a8 8 0 0 1-8 8 8.3 8.3 0 0 1-3.7-.86L4 20l.86-4.3A8.3 8.3 0 1 1 20 12Z"
                              />
                            </svg>
                          )}
                        </span>

                        <span
                          className={`min-w-0 flex-1 truncate text-xs ${
                            isSelected
                              ? "font-semibold text-slate-900"
                              : "font-medium text-slate-600 group-hover:text-slate-900"
                          }`}
                        >
                          {conversation.title ||
                            "New conversation"}
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={(event) =>
                          void handleDelete(
                            event,
                            conversation.id,
                          )
                        }
                        disabled={Boolean(
                          deletingConversationId,
                        )}
                        aria-label={`Delete ${
                          conversation.title ||
                          "conversation"
                        }`}
                        title="Delete conversation"
                        className="mr-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-300 opacity-0 transition hover:bg-red-50 hover:text-red-600 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500/20 group-hover:opacity-100"
                      >
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
                            d="M4 7h16M10 11v6m4-6v6M9 7V4h6v3m-9 0 1 13h8l1-13"
                          />
                        </svg>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
        </section>

        {/* Divider */}
        <div className="mx-4 my-5 border-t border-slate-200" />

        {/* Documents */}
        <section>
          <DocumentPanel />
        </section>
      </div>

      {/* ─────────────────────────────────────────
          ACCOUNT
      ───────────────────────────────────────── */}
      <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-3 py-3">
        <div className="flex items-center gap-2.5 rounded-xl px-2 py-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[11px] font-semibold text-white">
            {usernameInitial}
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-slate-800">
              {user?.username || "User"}
            </p>

            <p className="truncate text-[10px] text-slate-400">
              {user?.email || "Signed in"}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void logout()}
            title="Log out"
            aria-label="Log out"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
          >
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
                d="M10 17l5-5-5-5M15 12H3m9-7h6a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-6"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConversationSidebar;

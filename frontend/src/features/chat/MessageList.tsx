import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { getMessages } from "./api";
import SourceList from "./SourceList";

interface MessageListProps {
  conversationId: string;
  streamingContent?: string;
  isStreaming?: boolean;
}

function MessageList({
  conversationId,
  streamingContent = "",
  isStreaming = false,
}: MessageListProps) {
  const {
    data: messages = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => getMessages(conversationId),
  });

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-3xl space-y-8 py-8">
        {[1, 2, 3].map((item) => (
          <div
            key={item}
            className="flex gap-4"
            aria-hidden="true"
          >
            <div className="h-8 w-8 shrink-0 animate-pulse rounded-full bg-slate-200" />

            <div className="min-w-0 flex-1 space-y-3 pt-1">
              <div className="h-3 w-20 animate-pulse rounded bg-slate-200" />
              <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
              <div className="h-3 w-4/5 animate-pulse rounded bg-slate-100" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="w-full max-w-md rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
          <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-red-100 font-semibold text-red-600">
            !
          </div>

          <h2 className="text-sm font-semibold text-red-800">
            Unable to load messages
          </h2>

          <p className="mt-2 text-xs leading-5 text-red-600">
            We couldn't retrieve this conversation. Please try again.
          </p>

          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-4 rounded-lg border border-red-200 bg-white px-4 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-100 focus:outline-none focus:ring-4 focus:ring-red-500/10"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (messages.length === 0 && !streamingContent && !isStreaming) {
    return (
      <div className="flex min-h-[55vh] items-center justify-center">
        <div className="w-full max-w-lg text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-lg font-bold text-white shadow-lg shadow-slate-950/10">
            O
          </div>

          <h2 className="text-xl font-semibold tracking-tight text-slate-950">
            Start a conversation
          </h2>

          <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
            Ask OmniChat a question, explore an idea, or use your uploaded
            documents as context.
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
              Ask a question
            </span>

            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
              Analyze a document
            </span>

            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
              Brainstorm an idea
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 py-4 sm:py-6">
      {messages.map((message) => {
        const isUser = message.role === "user";

        return (
          <article
            key={message.id}
            className={`group flex gap-3 sm:gap-4 ${
              isUser ? "items-start" : "items-start"
            }`}
          >
            {/* Avatar */}
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
                isUser
                  ? "bg-slate-200 text-slate-700"
                  : "bg-slate-950 text-white"
              }`}
              aria-hidden="true"
            >
              {isUser ? "You" : "O"}
            </div>

            {/* Message */}
            <div className="min-w-0 flex-1">
              <div className="mb-1.5 flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-800">
                  {isUser ? "You" : "OmniChat"}
                </span>

                {!isUser && (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                    AI
                  </span>
                )}
              </div>

              <div
                className={`message-content max-w-none text-sm leading-7 sm:text-[15px] ${
                  isUser
                    ? "text-slate-700"
                    : "text-slate-800"
                }`}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ children, href, ...props }) => (
                      <a
                        {...props}
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-slate-900 underline decoration-slate-300 underline-offset-2 transition hover:decoration-slate-900"
                      >
                        {children}
                      </a>
                    ),

                    pre: ({ children }) => (
                      <pre className="my-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-950 p-4 text-sm leading-6 text-slate-100">
                        {children}
                      </pre>
                    ),

                    code: ({
                      className,
                      children,
                      ...props
                    }) => {
                      const isBlock = Boolean(className);

                      if (isBlock) {
                        return (
                          <code
                            className="font-mono text-[13px]"
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      }

                      return (
                        <code
                          className="rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[12px] text-slate-800"
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    },

                    table: ({ children }) => (
                      <div className="my-4 overflow-x-auto rounded-xl border border-slate-200">
                        <table className="min-w-full divide-y divide-slate-200 text-sm">
                          {children}
                        </table>
                      </div>
                    ),

                    th: ({ children }) => (
                      <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold text-slate-700">
                        {children}
                      </th>
                    ),

                    td: ({ children }) => (
                      <td className="border-t border-slate-100 px-4 py-3 align-top text-sm text-slate-600">
                        {children}
                      </td>
                    ),

                    blockquote: ({ children }) => (
                      <blockquote className="my-4 border-l-2 border-slate-300 pl-4 italic text-slate-500">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>

              {/* RAG sources */}
              {message.role === "assistant" &&
                message.sources.length > 0 && (
                  <div className="mt-4">
                    <SourceList sources={message.sources} />
                  </div>
                )}
            </div>
          </article>
        );
      })}

      {/* Streaming assistant response */}
      {isStreaming && (
        <article className="flex gap-3 sm:gap-4">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-950 text-[11px] font-semibold text-white"
            aria-hidden="true"
          >
            O
          </div>

          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-800">
                OmniChat
              </span>

              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                AI
              </span>
            </div>

            <div className="message-content text-sm leading-7 text-slate-800 sm:text-[15px]">
              {streamingContent ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                >
                  {streamingContent}
                </ReactMarkdown>
              ) : (
                <div className="flex items-center gap-1.5 py-2">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                </div>
              )}

              {streamingContent && (
                <span
                  aria-hidden="true"
                  className="ml-0.5 inline-block h-4 w-1.5 translate-y-0.5 animate-pulse rounded-sm bg-slate-500"
                />
              )}
            </div>
          </div>
        </article>
      )}
    </div>
  );
}

export default MessageList;
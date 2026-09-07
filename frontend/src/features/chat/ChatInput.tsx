import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import {
  streamMessage,
  type StreamStatus,
} from "./api";

interface ChatInputProps {
  conversationId: string;
  model?: string;
  onStreamStart: () => void;
  onStatus: (status: StreamStatus) => void;
  onToken: (token: string) => void;
  onMessageSent: () => void | Promise<void>;
  onStreamError: () => void;
}

function ChatInput({
  conversationId,
  model,
  onStreamStart,
  onStatus,
  onToken,
  onMessageSent,
  onStreamError,
}: ChatInputProps) {
  const [content, setContent] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const textareaRef =
    useRef<HTMLTextAreaElement>(null);

  /* ---------------------------------------------------------------------- */
  /* Auto resize                                                            */
  /* ---------------------------------------------------------------------- */

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";

    const nextHeight = Math.min(
      textarea.scrollHeight,
      192,
    );

    textarea.style.height = `${nextHeight}px`;
  }, [content]);

  /* ---------------------------------------------------------------------- */
  /* Submit                                                                 */
  /* ---------------------------------------------------------------------- */

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedContent = content.trim();

    if (!trimmedContent || isSending) {
      return;
    }

    setError("");
    setIsSending(true);
    setContent("");

    onStreamStart();

    await streamMessage(
      conversationId,
      trimmedContent,

      /* onStatus */
      (status) => {
        onStatus(status);
      },

      /* onToken */
      (token) => {
        onToken(token);
      },

      /* onComplete */
      async () => {
        try {
          await onMessageSent();
        } finally {
          setIsSending(false);

          window.setTimeout(() => {
            textareaRef.current?.focus();
          }, 0);
        }
      },

      /* onError */
      (streamError) => {
        console.error(
          "Failed to stream message:",
          streamError,
        );

        setError(streamError.message);
        setIsSending(false);

        onStreamError();

        window.setTimeout(() => {
          textareaRef.current?.focus();
        }, 0);
      },
      model,
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Keyboard                                                               */
  /* ---------------------------------------------------------------------- */

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      event.currentTarget.form?.requestSubmit();
    }
  }

  /* ---------------------------------------------------------------------- */
  /* Content                                                                */
  /* ---------------------------------------------------------------------- */

  function handleContentChange(
    value: string,
  ) {
    setContent(value);

    if (error) {
      setError("");
    }
  }

  const canSend =
    Boolean(content.trim()) && !isSending;

  return (
    <div className="w-full">
      {/* ------------------------------------------------------------------ */}
      {/* Error                                                              */}
      {/* ------------------------------------------------------------------ */}

      {error && (
        <div
          role="alert"
          className="mb-2.5 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 shadow-sm"
        >
          <span
            aria-hidden="true"
            className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-[11px] font-bold text-red-600"
          >
            !
          </span>

          <span className="min-w-0 flex-1 text-xs leading-5 text-red-700">
            {error}
          </span>

          <button
            type="button"
            onClick={() => setError("")}
            aria-label="Dismiss error"
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-red-400 transition hover:bg-red-100 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-500/20"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="h-3.5 w-3.5"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                d="M6 6l12 12M18 6 6 18"
              />
            </svg>
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Composer                                                           */}
      {/* ------------------------------------------------------------------ */}

      <form
        onSubmit={handleSubmit}
        className="
          rounded-[22px]
          border
          border-slate-200
          bg-white
          p-2
          shadow-[0_8px_30px_rgba(15,23,42,0.08)]
          transition-all
          duration-200
          hover:border-slate-300
          hover:shadow-[0_10px_35px_rgba(15,23,42,0.09)]
          focus-within:border-blue-200
          focus-within:shadow-[0_12px_40px_rgba(37,99,235,0.10)]
        "
      >
        {/* Input row */}
        <div className="flex items-end gap-2">
          {/* Decorative composer icon */}
          <div className="mb-1.5 hidden h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-400 sm:flex">
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
                d="M12 3v18M3 12h18"
              />
            </svg>
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(event) =>
              handleContentChange(
                event.target.value,
              )
            }
            onKeyDown={handleKeyDown}
            placeholder={
              isSending
                ? "OmniChat is thinking..."
                : "Message OmniChat..."
            }
            rows={1}
            disabled={isSending}
            aria-label="Message OmniChat"
            className="
              max-h-48
              min-h-11
              flex-1
              resize-none
              overflow-y-auto
              bg-transparent
              px-2.5
              py-2.5
              text-[15px]
              leading-6
              text-slate-900
              outline-none
              placeholder:text-slate-400
              disabled:cursor-not-allowed
              disabled:text-slate-400
            "
          />

          {/* Send */}
          <button
            type="submit"
            disabled={!canSend}
            aria-label={
              isSending
                ? "Generating response"
                : "Send message"
            }
            title={
              isSending
                ? "Generating response"
                : canSend
                  ? "Send message"
                  : "Type a message to send"
            }
            className={`
              mb-1
              flex
              h-10
              w-10
              shrink-0
              items-center
              justify-center
              rounded-xl
              transition-all
              duration-150
              focus:outline-none
              focus:ring-4
              focus:ring-blue-500/15
              ${
                canSend
                  ? "bg-slate-950 text-white shadow-sm hover:bg-slate-800 hover:shadow-md active:scale-95"
                  : "cursor-not-allowed bg-slate-100 text-slate-300"
              }
            `}
          >
            {isSending ? (
              <span
                aria-hidden="true"
                className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
              />
            ) : (
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
                  d="M12 19V5m0 0-6 6m6-6 6 6"
                />
              </svg>
            )}
          </button>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 px-2.5 pb-1 pt-1">
          <div className="flex min-w-0 items-center gap-1.5">
            <span
              className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                isSending
                  ? "animate-pulse bg-blue-500"
                  : "bg-emerald-500"
              }`}
            />

            <span className="truncate text-[10px] text-slate-400">
              {isSending
                ? "Generating a response..."
                : "AI responses may contain mistakes."}
            </span>
          </div>

          <span className="hidden shrink-0 text-[10px] text-slate-400 sm:block">
            Enter to send
            <span className="mx-1 text-slate-300">
              ·
            </span>
            Shift + Enter for new line
          </span>
        </div>
      </form>

      {/* Hint */}
      <div className="mt-2 flex items-center justify-center px-2">
        <p className="text-[10px] text-slate-400">
          Ask anything or ask about your uploaded
          documents.
        </p>
      </div>
    </div>
  );
}

export default ChatInput;

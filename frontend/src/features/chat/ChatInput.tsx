import {
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { streamMessage } from "./api";

interface ChatInputProps {
  conversationId: string;
  onStreamStart: () => void;
  onToken: (token: string) => void;
  onMessageSent: () => void;
  onStreamError: () => void;
}

function ChatInput({
  conversationId,
  onStreamStart,
  onToken,
  onMessageSent,
  onStreamError,
}: ChatInputProps) {
  const [content, setContent] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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
      (token) => {
        onToken(token);
      },
      () => {
        onMessageSent();
        setIsSending(false);
      },
      (streamError) => {
        console.error("Failed to stream message:", streamError);

        setError(streamError.message);
        setIsSending(false);

        onStreamError();
      },
    );
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const canSend = Boolean(content.trim()) && !isSending;

  return (
    <div className="w-full">
      {error && (
        <div
          role="alert"
          className="mb-2 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-700 shadow-sm"
        >
          <span
            aria-hidden="true"
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 font-semibold text-red-600"
          >
            !
          </span>

          <span className="min-w-0 flex-1">
            {error}
          </span>

          <button
            type="button"
            onClick={() => setError("")}
            aria-label="Dismiss error"
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-red-400 transition hover:bg-red-100 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-500/20"
          >
            ×
          </button>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_8px_30px_rgba(15,23,42,0.08)] transition focus-within:border-slate-300 focus-within:shadow-[0_10px_35px_rgba(15,23,42,0.10)]"
      >
        <div className="flex items-end gap-2">
          <textarea
            value={content}
            onChange={(event) => {
              setContent(event.target.value);

              if (error) {
                setError("");
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              isSending
                ? "OmniChat is thinking..."
                : "Message OmniChat..."
            }
            rows={1}
            disabled={isSending}
            aria-label="Message OmniChat"
            className="max-h-48 min-h-11 flex-1 resize-none overflow-y-auto bg-transparent px-3 py-2.5 text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed disabled:text-slate-400"
          />

          <button
            type="submit"
            disabled={!canSend}
            aria-label={
              isSending
                ? "Generating response"
                : "Send message"
            }
            className={`mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white transition focus:outline-none focus:ring-4 focus:ring-slate-900/15 ${
              canSend
                ? "bg-slate-950 hover:bg-slate-800 active:scale-95"
                : "cursor-not-allowed bg-slate-200 text-slate-400"
            }`}
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

        <div className="flex items-center justify-between px-3 pb-1 pt-1">
          <span className="text-[11px] text-slate-400">
            {isSending
              ? "Generating a response..."
              : "AI responses may contain mistakes."}
          </span>

          <span className="hidden text-[11px] text-slate-400 sm:block">
            Enter to send · Shift + Enter for new line
          </span>
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
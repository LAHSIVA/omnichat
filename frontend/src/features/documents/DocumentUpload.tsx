import {
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { uploadDocument } from "./api";

function DocumentUpload() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const selectedFile = event.target.files?.[0] ?? null;

    setFile(selectedFile);
    setError("");
  }

  function handleClose() {
    if (isUploading) {
      return;
    }

    setIsOpen(false);
    setError("");
    setTitle("");
    setFile(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!file) {
      setError("Please select a document.");
      return;
    }

    setError("");
    setIsUploading(true);

    try {
      await uploadDocument(
        title.trim() || file.name,
        file,
      );

      setTitle("");
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });

      setIsOpen(false);
    } catch (uploadError) {
      console.error(
        "Failed to upload document:",
        uploadError,
      );

      setError(
        "Unable to upload document. Please try again.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <>
      {/* Upload trigger */}
      <button
        type="button"
        onClick={() => {
          setError("");
          setIsOpen(true);
        }}
        aria-label="Upload document"
        title="Upload document"
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-900/10 active:scale-95"
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
            strokeLinejoin="round"
            d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14"
          />
        </svg>
      </button>

      {/* Upload dialog */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/30 px-4 backdrop-blur-[2px]"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              handleClose();
            }
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-upload-title"
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_24px_70px_rgba(15,23,42,0.18)]"
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-white">
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
                      d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14"
                    />
                  </svg>
                </div>

                <h2
                  id="document-upload-title"
                  className="text-base font-semibold tracking-tight text-slate-950"
                >
                  Add a document
                </h2>

                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Upload a document and use it as knowledge when chatting
                  with OmniChat.
                </p>
              </div>

              <button
                type="button"
                onClick={handleClose}
                disabled={isUploading}
                aria-label="Close upload dialog"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:opacity-40"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-6 space-y-4"
            >
              {/* File selection */}
              <div>
                <label
                  htmlFor="document-file"
                  className="mb-2 block text-xs font-semibold text-slate-700"
                >
                  Document
                </label>

                <input
                  ref={fileInputRef}
                  id="document-file"
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={handleFileChange}
                  disabled={isUploading}
                  className="sr-only"
                />

                <button
                  type="button"
                  disabled={isUploading}
                  onClick={() => fileInputRef.current?.click()}
                  className="flex min-h-24 w-full flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center transition hover:border-slate-400 hover:bg-slate-100 focus:outline-none focus:ring-4 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {file ? (
                    <>
                      <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-600 shadow-sm">
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
                            d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M14 3v5h5"
                          />
                        </svg>
                      </div>

                      <span className="max-w-full truncate text-xs font-semibold text-slate-700">
                        {file.name}
                      </span>

                      <span className="mt-1 text-[10px] text-slate-400">
                        Click to choose another file
                      </span>
                    </>
                  ) : (
                    <>
                      <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-400 shadow-sm">
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
                            d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14"
                          />
                        </svg>
                      </div>

                      <span className="text-xs font-semibold text-slate-700">
                        Choose a document
                      </span>

                      <span className="mt-1 text-[10px] text-slate-400">
                        PDF, TXT, or DOCX
                      </span>
                    </>
                  )}
                </button>
              </div>

              {/* Title */}
              <div>
                <label
                  htmlFor="document-title"
                  className="mb-2 block text-xs font-semibold text-slate-700"
                >
                  Title
                  <span className="ml-2 font-normal text-slate-400">
                    Optional
                  </span>
                </label>

                <input
                  id="document-title"
                  type="text"
                  placeholder="e.g. Project specification"
                  value={title}
                  onChange={(event) => {
                    setTitle(event.target.value);
                    if (error) {
                      setError("");
                    }
                  }}
                  disabled={isUploading}
                  className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-xs text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:bg-slate-50"
                />
              </div>

              {/* Error */}
              {error && (
                <div
                  role="alert"
                  className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-700"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 font-semibold text-red-600">
                    !
                  </span>

                  <span>{error}</span>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isUploading}
                  className="h-10 rounded-xl px-4 text-xs font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={!file || isUploading}
                  className="flex h-10 min-w-28 items-center justify-center rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-900/15 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
                >
                  {isUploading ? (
                    <>
                      <span
                        aria-hidden="true"
                        className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white"
                      />
                      Uploading...
                    </>
                  ) : (
                    "Upload document"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default DocumentUpload;
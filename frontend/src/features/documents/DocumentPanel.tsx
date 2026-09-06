import { useQuery, useQueryClient } from "@tanstack/react-query";
import DocumentUpload from "./DocumentUpload";
import {
  deleteDocument,
  getDocuments,
  retryDocument,
} from "./api";

function DocumentPanel() {
  const queryClient = useQueryClient();

  const {
    data: documents = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  async function handleDelete(documentId: number) {
    const confirmed = window.confirm(
      "Delete this document? Its indexed knowledge will also be removed.",
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteDocument(documentId);

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    } catch (error) {
      console.error("Failed to delete document:", error);
    }
  }

  async function handleRetry(documentId: number) {
    try {
      await retryDocument(documentId);

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    } catch (error) {
      console.error("Failed to retry document:", error);
    }
  }

  function getStatusStyles(status: string) {
    switch (status) {
      case "completed":
        return {
          dot: "bg-emerald-500",
          text: "text-emerald-700",
          label: "Ready",
        };

      case "processing":
        return {
          dot: "bg-amber-500 animate-pulse",
          text: "text-amber-700",
          label: "Processing",
        };

      case "pending":
        return {
          dot: "bg-slate-400",
          text: "text-slate-500",
          label: "Queued",
        };

      case "failed":
        return {
          dot: "bg-red-500",
          text: "text-red-700",
          label: "Failed",
        };

      default:
        return {
          dot: "bg-slate-400",
          text: "text-slate-500",
          label: status,
        };
    }
  }

  function getFileExtension(filename: string) {
    const extension = filename.split(".").pop()?.toLowerCase();

    if (extension === "pdf") {
      return "PDF";
    }

    if (extension === "docx") {
      return "DOCX";
    }

    if (extension === "txt") {
      return "TXT";
    }

    return "FILE";
  }

  return (
    <section className="border-t border-slate-200/80 bg-slate-50/70">
      {/* Section header */}
      <div className="px-4 pb-3 pt-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-[18px] w-[18px]"
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
                  d="M14 3v5h5M9 13h6M9 17h4"
                />
              </svg>
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-[13px] font-semibold tracking-[-0.01em] text-slate-800">
                  Knowledge
                </h2>

                {!isLoading && !isError && documents.length > 0 && (
                  <span className="rounded-full bg-slate-200/80 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                    {documents.length}
                  </span>
                )}
              </div>

              <p className="mt-0.5 text-[11px] leading-4 text-slate-400">
                Documents available to your chats
              </p>
            </div>
          </div>

          <DocumentUpload />
        </div>
      </div>

      {/* Upload guidance */}
      <div className="px-3 pb-3">
        <div className="flex items-center gap-2.5 rounded-xl border border-dashed border-slate-300 bg-white/80 px-3 py-2.5 transition-colors hover:border-slate-400 hover:bg-white">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
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
                d="M12 16V8m0 0-3 3m3-3 3 3"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 20h14a2 2 0 0 0 2-2V9.5L15.5 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2Z"
              />
            </svg>
          </div>

          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-medium text-slate-600">
              Add knowledge to your workspace
            </p>

            <p className="mt-0.5 text-[10px] text-slate-400">
              PDF, DOCX or TXT
            </p>
          </div>

          <span className="shrink-0 text-[10px] font-medium text-slate-400">
            Upload above
          </span>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-2 px-3 pb-4">
          {[1, 2].map((item) => (
            <div
              key={item}
              className="rounded-xl border border-slate-200/70 bg-white p-3"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 shrink-0 animate-pulse rounded-lg bg-slate-200" />

                <div className="min-w-0 flex-1 space-y-2">
                  <div className="h-3 w-3/4 animate-pulse rounded bg-slate-200" />
                  <div className="h-2.5 w-1/2 animate-pulse rounded bg-slate-100" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="mx-3 mb-4 rounded-xl border border-red-200 bg-red-50/70 p-3.5">
          <div className="flex items-start gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-red-100 text-xs font-bold text-red-600">
              !
            </div>

            <div className="min-w-0">
              <p className="text-[12px] font-semibold text-red-700">
                Unable to load documents
              </p>

              <p className="mt-0.5 text-[11px] leading-4 text-red-600/80">
                Something went wrong while loading your knowledge.
              </p>

              <button
                type="button"
                onClick={() => void refetch()}
                className="mt-2 text-[11px] font-semibold text-red-700 underline underline-offset-2 transition hover:text-red-800"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && documents.length === 0 && (
        <div className="mx-3 mb-4 rounded-xl border border-slate-200 bg-white px-4 py-5 text-center shadow-sm">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              className="h-5 w-5"
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

          <p className="mt-3 text-[12px] font-semibold text-slate-700">
            Your knowledge base is empty
          </p>

          <p className="mx-auto mt-1 max-w-[220px] text-[11px] leading-4 text-slate-400">
            Upload a document to let OmniChat answer questions using
            information from your files.
          </p>
        </div>
      )}

      {/* Document list */}
      {!isLoading && !isError && documents.length > 0 && (
        <div className="space-y-2 px-3 pb-4">
          {documents.map((document) => {
            const status = getStatusStyles(document.status);
            const filename =
              document.title || document.original_filename;

            return (
              <article
                key={document.id}
                className="group rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition-all duration-150 hover:border-slate-300 hover:shadow-md"
              >
                <div className="flex min-w-0 items-start gap-3">
                  {/* File type */}
                  <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-lg border border-slate-200 bg-slate-50">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      className="h-4 w-4 text-slate-500"
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

                    <span className="mt-0.5 text-[7px] font-bold tracking-wide text-slate-400">
                      {getFileExtension(document.original_filename)}
                    </span>
                  </div>

                  {/* Document information */}
                  <div className="min-w-0 flex-1">
                    <p
                      className="truncate text-[12px] font-semibold leading-5 text-slate-700"
                      title={filename}
                    >
                      {filename}
                    </p>

                    <p
                      className="mt-0.5 truncate text-[10px] leading-4 text-slate-400"
                      title={document.original_filename}
                    >
                      {document.original_filename}
                    </p>

                    <div className="mt-2 flex items-center gap-2">
                      <span
                        className={`h-1.5 w-1.5 shrink-0 rounded-full ${status.dot}`}
                      />

                      <span
                        className={`text-[10px] font-medium ${status.text}`}
                      >
                        {status.label}
                      </span>
                    </div>
                  </div>

                  {/* Delete */}
                  <button
                    type="button"
                    onClick={() => void handleDelete(document.id)}
                    aria-label={`Delete ${filename}`}
                    title="Delete document"
                    className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-600 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500/20 group-hover:opacity-100"
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

                {/* Processing */}
                {document.status === "processing" && (
                  <div className="mt-3">
                    <div className="mb-1.5 flex items-center justify-between">
                      <span className="text-[9px] text-slate-400">
                        Indexing document...
                      </span>

                      <span className="text-[9px] text-slate-400">
                        Please wait
                      </span>
                    </div>

                    <div className="h-1 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full w-1/2 animate-[pulse_1.5s_ease-in-out_infinite] rounded-full bg-slate-400" />
                    </div>
                  </div>
                )}

                {/* Failed */}
                {document.status === "failed" && (
                  <div className="mt-3 flex items-center justify-between gap-3 rounded-lg bg-red-50 px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-[10px] font-medium text-red-700">
                        Processing failed
                      </p>

                      <p className="mt-0.5 text-[9px] text-red-500">
                        The document could not be indexed.
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => void handleRetry(document.id)}
                      className="shrink-0 rounded-md px-2.5 py-1.5 text-[10px] font-semibold text-red-700 transition hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500/20"
                    >
                      Retry
                    </button>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default DocumentPanel;

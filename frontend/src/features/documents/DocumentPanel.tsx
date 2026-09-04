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
          badge: "bg-emerald-50 text-emerald-700",
          label: "Ready",
        };

      case "processing":
        return {
          dot: "bg-amber-500 animate-pulse",
          badge: "bg-amber-50 text-amber-700",
          label: "Processing",
        };

      case "pending":
        return {
          dot: "bg-slate-400",
          badge: "bg-slate-100 text-slate-600",
          label: "Queued",
        };

      case "failed":
        return {
          dot: "bg-red-500",
          badge: "bg-red-50 text-red-700",
          label: "Failed",
        };

      default:
        return {
          dot: "bg-slate-400",
          badge: "bg-slate-100 text-slate-600",
          label: status,
        };
    }
  }

  return (
    <section className="flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pb-2 pt-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-600">
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
                d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14 3v5h5M9 13h6M9 17h6"
              />
            </svg>
          </div>

          <div className="min-w-0">
            <h2 className="text-xs font-semibold text-slate-700">
              Documents
            </h2>

            {!isLoading &&
              !isError &&
              documents.length > 0 && (
                <p className="text-[10px] text-slate-400">
                  {documents.length}{" "}
                  {documents.length === 1
                    ? "document"
                    : "documents"}
                </p>
              )}
          </div>
        </div>

        <DocumentUpload />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-1.5 px-3 pb-3">
          {[1, 2].map((item) => (
            <div
              key={item}
              className="flex items-center gap-2 rounded-xl bg-white p-2.5"
            >
              <div className="h-8 w-8 shrink-0 animate-pulse rounded-lg bg-slate-200" />

              <div className="min-w-0 flex-1 space-y-2">
                <div className="h-2.5 w-3/4 animate-pulse rounded bg-slate-200" />
                <div className="h-2 w-1/2 animate-pulse rounded bg-slate-100" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="mx-3 mb-3 rounded-xl border border-red-200 bg-red-50 p-3">
          <div className="flex items-start gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-[10px] font-bold text-red-600">
              !
            </span>

            <div className="min-w-0">
              <p className="text-xs font-medium text-red-700">
                Unable to load documents
              </p>

              <button
                type="button"
                onClick={() => void refetch()}
                className="mt-1.5 text-[11px] font-semibold text-red-700 underline underline-offset-2 hover:text-red-800"
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
        documents.length === 0 && (
          <div className="mx-3 mb-3 rounded-xl border border-dashed border-slate-200 bg-white/60 px-3 py-4 text-center">
            <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-400">
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
                  d="M12 16V8m0 0-3 3m3-3 3 3M5 20h14a2 2 0 0 0 2-2V9.5L15.5 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2Z"
                />
              </svg>
            </div>

            <p className="text-[11px] font-medium text-slate-600">
              No documents yet
            </p>

            <p className="mt-0.5 text-[10px] leading-4 text-slate-400">
              Upload a PDF, TXT, or DOCX to ask questions about it.
            </p>
          </div>
        )}

      {/* Document list */}
      {!isLoading &&
        !isError &&
        documents.length > 0 && (
          <div className="space-y-1.5 px-3 pb-3">
            {documents.map((document) => {
              const status = getStatusStyles(document.status);

              return (
                <article
                  key={document.id}
                  className="group rounded-xl border border-slate-200/80 bg-white p-2.5 transition hover:border-slate-300 hover:shadow-sm"
                >
                  <div className="flex min-w-0 items-start gap-2.5">
                    {/* File icon */}
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
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
                          d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M14 3v5h5"
                        />
                      </svg>
                    </div>

                    {/* Information */}
                    <div className="min-w-0 flex-1">
                      <p
                        className="truncate text-[11px] font-semibold text-slate-700"
                        title={
                          document.title ||
                          document.original_filename
                        }
                      >
                        {document.title ||
                          document.original_filename}
                      </p>

                      <p
                        className="mt-0.5 truncate text-[10px] text-slate-400"
                        title={document.original_filename}
                      >
                        {document.original_filename}
                      </p>

                      <div className="mt-1.5 flex items-center gap-1.5">
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${status.dot}`}
                        />

                        <span
                          className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${status.badge}`}
                        >
                          {status.label}
                        </span>
                      </div>
                    </div>

                    {/* Delete */}
                    <button
                      type="button"
                      onClick={() =>
                        void handleDelete(document.id)
                      }
                      aria-label={`Delete ${
                        document.title ||
                        document.original_filename
                      }`}
                      title="Delete document"
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-300 opacity-0 transition hover:bg-red-50 hover:text-red-600 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500/20 group-hover:opacity-100"
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

                  {/* Failed state */}
                  {document.status === "failed" && (
                    <div className="mt-2 flex items-center justify-between rounded-lg bg-red-50 px-2.5 py-2">
                      <span className="text-[10px] text-red-600">
                        Processing failed
                      </span>

                      <button
                        type="button"
                        onClick={() =>
                          void handleRetry(document.id)
                        }
                        className="rounded-md px-2 py-1 text-[10px] font-semibold text-red-700 transition hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500/20"
                      >
                        Retry
                      </button>
                    </div>
                  )}

                  {/* Processing state */}
                  {document.status === "processing" && (
                    <div className="mt-2 h-1 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full w-1/2 animate-[pulse_1.5s_ease-in-out_infinite] rounded-full bg-slate-400" />
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
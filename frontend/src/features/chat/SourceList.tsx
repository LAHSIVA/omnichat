import type { MessageSource } from "./types";

interface SourceListProps {
  sources: MessageSource[];
}

function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="source-list">
      <strong>Sources</strong>

      {sources.map((source) => (
        <div
          key={`${source.document_id}-${source.chunk_index}`}
          className="source-item"
        >
          <div>
            📄 {source.document_title}
          </div>

          <small>
            {source.original_filename} · Chunk{" "}
            {source.chunk_index}
          </small>

          {source.distance !== null && (
            <small>
              Similarity distance:{" "}
              {source.distance.toFixed(3)}
            </small>
          )}
        </div>
      ))}
    </div>
  );
}

export default SourceList;
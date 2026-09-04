from ai.domain.types import RetrievedChunk


def test_retrieved_chunk_contains_source_metadata():
    chunk = RetrievedChunk(
        content="Predictive maintenance detects failures.",
        document_id=1,
        document_title="Predictive Maintenance",
        original_filename="predictive_maintenance.txt",
        chunk_index=0,
        chunk_id=1,
        distance=0.12,
    )

    assert chunk.content == (
        "Predictive maintenance detects failures."
    )
    assert chunk.document_id == 1
    assert chunk.document_title == "Predictive Maintenance"
    assert chunk.original_filename == "predictive_maintenance.txt"
    assert chunk.chunk_index == 0
    assert chunk.distance == 0.12
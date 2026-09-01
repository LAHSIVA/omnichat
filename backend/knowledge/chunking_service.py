from knowledge.chunking import TextChunker
from knowledge.models import Document, DocumentChunk


class DocumentChunkingService:
    def __init__(self, chunker=None):
        self.chunker = chunker or TextChunker()

    def create_chunks(self, document):
        chunks = self.chunker.chunk(
            document.extracted_text,
        )

        DocumentChunk.objects.filter(
            document=document,
        ).delete()

        return DocumentChunk.objects.bulk_create(
            [
                DocumentChunk(
                    document=document,
                    content=content,
                    chunk_index=index,
                )
                for index, content in enumerate(chunks)
            ]
        )
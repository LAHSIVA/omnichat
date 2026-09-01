from knowledge.chunking_service import DocumentChunkingService
from knowledge.embeddings import OllamaEmbeddingProvider
from knowledge.extractors import DocumentExtractorFactory
from knowledge.models import Document, DocumentChunk

class DocumentProcessingService:
    def __init__(
        self,
        chunking_service=None,
        embedding_provider=None,
    ):
        self.chunking_service = (
            chunking_service
            or DocumentChunkingService()
        )

        self.embedding_provider = (
            embedding_provider
            or OllamaEmbeddingProvider()
        )

    def process(self, document):
        document.status = Document.Status.PROCESSING
        document.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        try:
            extractor = DocumentExtractorFactory.get_extractor(
                document.content_type,
            )

            text = extractor.extract(document)

            document.extracted_text = text

            chunks = self.chunking_service.create_chunks(
                document,
            )

            embeddings = self.embedding_provider.embed(
                [chunk.content for chunk in chunks]
            )

            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                DocumentChunk.objects.bulk_update(
                chunks,
                ["embedding", "updated_at"],
            )

            document.status = Document.Status.COMPLETED

            document.save(
                update_fields=[
                    "extracted_text",
                    "status",
                    "updated_at",
                ]
            )

            return text

        except Exception:
            document.status = Document.Status.FAILED
            document.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise
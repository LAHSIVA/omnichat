from knowledge.models import Document
from knowledge.services import DocumentProcessingService


def process_document(
    document_id,
    processing_service=None,
):
    document = Document.objects.get(
        id=document_id,
    )

    service = (
        processing_service
        or DocumentProcessingService()
    )

    return service.process(document)
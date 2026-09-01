from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentTypeError(Exception):
    """The document type is not supported for text extraction."""


class DocumentTextExtractor:
    def extract(self, document):
        raise NotImplementedError


class PlainTextExtractor(DocumentTextExtractor):
    def extract(self, document):
        with document.file.open("rb") as file:
            content = file.read()

        return content.decode("utf-8")


class PDFExtractor(DocumentTextExtractor):
    def extract(self, document):
        with document.file.open("rb") as file:
            reader = PdfReader(file)

            pages = []

            for page in reader.pages:
                text = page.extract_text()

                if text:
                    pages.append(text)

        return "\n\n".join(pages)


class DOCXExtractor(DocumentTextExtractor):
    def extract(self, document):
        with document.file.open("rb") as file:
            docx = DocxDocument(file)

        paragraphs = [
            paragraph.text
            for paragraph in docx.paragraphs
            if paragraph.text
        ]

        return "\n\n".join(paragraphs)


class DocumentExtractorFactory:
    _extractors = {
        "text/plain": PlainTextExtractor,
        "application/pdf": PDFExtractor,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXExtractor,
    }

    @classmethod
    def get_extractor(cls, content_type):
        extractor_class = cls._extractors.get(content_type)

        if extractor_class is None:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type: {content_type}"
            )

        return extractor_class()
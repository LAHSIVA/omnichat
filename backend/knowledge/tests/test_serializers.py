import pytest
from knowledge.models import Document
from knowledge.serializers import DocumentSerializer


def test_document_serializer_exposes_expected_fields():
    assert set(DocumentSerializer.Meta.fields) == {
        "id",
        "title",
        "file",
        "original_filename",
        "content_type",
        "status",
        "created_at",
        "updated_at",
    }


def test_document_serializer_marks_server_fields_read_only():
    assert set(DocumentSerializer.Meta.read_only_fields) == {
        "id",
        "original_filename",
        "content_type",
        "status",
        "created_at",
        "updated_at",
    }


def test_document_serializer_rejects_blank_title():
    serializer = DocumentSerializer(
        data={
            "title": "   ",
        },
    )

    assert not serializer.is_valid()

    assert "title" in serializer.errors
    assert str(serializer.errors["title"][0]) == (
        "Title cannot be empty."
    )
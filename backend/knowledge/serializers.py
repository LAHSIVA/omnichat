from django.conf import settings
from rest_framework import serializers

from knowledge.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        max_length=255,
        allow_blank=True,
    )

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file",
            "original_filename",
            "content_type",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "content_type",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Title cannot be empty."
            )

        return value

    def validate_file(self, value):
        allowed_content_types = {
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }

        if value.content_type not in allowed_content_types:
            raise serializers.ValidationError(
                "Unsupported file type."
            )

        if value.size > settings.KNOWLEDGE_MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "File size exceeds the maximum allowed limit."
            )

        return value
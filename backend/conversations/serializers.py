from rest_framework import serializers

from .models import Conversation, Message, MessageSource


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class MessageSourceSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(
        source="document.title",
        read_only=True,
    )

    original_filename = serializers.CharField(
        source="document.original_filename",
        read_only=True,
    )

    chunk_index = serializers.IntegerField(
        source="chunk.chunk_index",
        read_only=True,
    )

    class Meta:
        model = MessageSource
        fields = [
            "document_id",
            "document_title",
            "original_filename",
            "chunk_index",
            "distance",
        ]


class MessageSerializer(serializers.ModelSerializer):
    sources = MessageSourceSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "created_at",
            "sources",
        ]
        read_only_fields = [
            "id",
            "role",
            "created_at",
            "sources",
        ]


class SourceSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    original_filename = serializers.CharField()
    chunk_index = serializers.IntegerField()
    distance = serializers.FloatField(
        allow_null=True,
    )


class ChatResponseSerializer(serializers.Serializer):
    message = MessageSerializer()
    sources = SourceSerializer(
        many=True,
    )


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(
        min_length=1,
        trim_whitespace=True,
    )
import uuid

from django.db import models


class Conversation(models.Model):
    """A chat conversation owned by an authenticated user."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or "Untitled conversation"


class Message(models.Model):
    """A single message within a conversation."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class MessageSource(models.Model):
    """A knowledge chunk used to generate an assistant message."""

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="sources",
    )

    document = models.ForeignKey(
        "knowledge.Document",
        on_delete=models.CASCADE,
        related_name="message_sources",
    )

    chunk = models.ForeignKey(
        "knowledge.DocumentChunk",
        on_delete=models.CASCADE,
        related_name="message_sources",
    )

    distance = models.FloatField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.message_id} - "
            f"{self.document.title} - "
            f"chunk {self.chunk.chunk_index}"
        )
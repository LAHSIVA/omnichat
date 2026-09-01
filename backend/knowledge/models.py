from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="documents/%Y/%m/%d/",
    )

    original_filename = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=100,
    )

    extracted_text = models.TextField(
    blank=True,
    default="",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    content = models.TextField()

    chunk_index = models.PositiveIntegerField()

    embedding = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="unique_document_chunk_index",
            ),
        ]

    def __str__(self):
        return f"{self.document.title} - chunk {self.chunk_index}"
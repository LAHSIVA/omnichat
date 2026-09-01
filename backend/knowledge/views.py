from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from knowledge.models import Document
from knowledge.serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES["file"]

        serializer.save(
            user=self.request.user,
            original_filename=uploaded_file.name,
            content_type=uploaded_file.content_type or "",
        )

class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            user=self.request.user
        )
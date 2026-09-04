from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from knowledge.models import Document
from knowledge.serializers import DocumentSerializer
from knowledge.tasks import process_document_task
from drf_spectacular.utils import extend_schema
class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES["file"]

        document = serializer.save(
            user=self.request.user,
            original_filename=uploaded_file.name,
            content_type=uploaded_file.content_type or "",
        )

        process_document_task.delay(document.id)


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            user=self.request.user
        )


class DocumentRetryView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        request=None,
        responses={202: DocumentSerializer},
    )
    def post(self, request, pk):
        document = get_object_or_404(
            Document,
            id=pk,
            user=request.user,
        )

        if document.status != Document.Status.FAILED:
            return Response(
                {
                    "detail": (
                        "Only failed documents can be retried."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = Document.Status.PENDING
        document.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        process_document_task.delay(document.id)

        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_202_ACCEPTED,
        )
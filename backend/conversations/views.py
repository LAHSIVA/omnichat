import json

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.orchestrator import ChatOrchestrator

from .models import Conversation
from .serializers import (
    ChatResponseSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)
from .title_service import generate_conversation_title
from ai.domain.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)

@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
            )
        ]
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
            )
        ]
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
            )
        ]
    ),
    destroy=extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
            )
        ]
    ),
)
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ConversationMessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, conversation_id):
        return get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
        )

    @extend_schema(
        responses=MessageSerializer(many=True),
    )
    def get(self, request, conversation_id):
        conversation = self.get_conversation(
            request,
            conversation_id,
        )

        messages = conversation.messages.all()

        serializer = MessageSerializer(
            messages,
            many=True,
        )

        return Response(serializer.data)

    @extend_schema(
        request=MessageCreateSerializer,
        responses={201: ChatResponseSerializer},
    )
    def post(self, request, conversation_id):
        conversation = self.get_conversation(
            request,
            conversation_id,
        )

        serializer = MessageCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        orchestrator = ChatOrchestrator()

        content = serializer.validated_data["content"]

        if not conversation.title:
            conversation.title = generate_conversation_title(content)
            conversation.save(
                update_fields=["title", "updated_at"]
            )

        result = orchestrator.chat(
            conversation=conversation,
            content=content,
        )

        response_data = {
            "message": MessageSerializer(
                result.assistant_message
            ).data,
            "sources": result.sources,
        }

        return Response(
            ChatResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationMessageStreamView(APIView):
    """
    Stream an assistant response using Server-Sent Events.
    """

    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, conversation_id):
        return get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
        )

    def post(self, request, conversation_id):
        conversation = self.get_conversation(
            request,
            conversation_id,
        )

        serializer = MessageCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data["content"]

        if not conversation.title:
            conversation.title = generate_conversation_title(content)
            conversation.save(
                update_fields=["title", "updated_at"]
            )

        def event_stream():
            orchestrator = ChatOrchestrator()

            try:
                for event in orchestrator.chat_stream(
                    conversation=conversation,
                    content=content,
                ):
                    event_type = event["type"]

                    event_data = {
                        key: value
                        for key, value in event.items()
                        if key != "type"
                    }

                    yield self.format_event(event_type, event_data)

            except Exception as exc:
                yield self.format_event(
                    "error",
                    {
                        "message": self.get_error_message(exc),
                    },
                )

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )

        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"

        return response

    @staticmethod
    def format_event(event_type, data):
        payload = {
            "type": event_type,
            **data,
        }

        return f"data: {json.dumps(payload, default=str)}\n\n"

    @staticmethod
    def get_error_message(exc):
        if isinstance(exc, LLMRateLimitError):
            return (
                "The AI service is temporarily rate-limited. "
                "Please try again shortly."
            )

        if isinstance(exc, LLMTimeoutError):
            return (
                "The AI service took too long to respond. "
                "Please try again."
            )

        if isinstance(exc, LLMProviderError):
            return (
                "The AI service is temporarily unavailable. "
                "Please try again shortly."
            )

        return "Unable to generate a response. Please try again."

    @staticmethod
    def get_error_message(exc):
        if isinstance(exc, LLMRateLimitError):
            return "The AI service is temporarily rate-limited. Please try again shortly."

        if isinstance(exc, LLMTimeoutError):
            return "The AI service took too long to respond. Please try again."

        if isinstance(exc, LLMProviderError):
            return "The AI service is temporarily unavailable. Please try again shortly."

        return "Unable to generate a response. Please try again."
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .serializers import ConversationSerializer

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import (
    MessageCreateSerializer,
    MessageSerializer,
)

from ai.orchestrator import ChatOrchestrator
from drf_spectacular.utils import extend_schema


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
        responses={201: MessageSerializer},
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

        result = orchestrator.chat(
            conversation=conversation,
            content=serializer.validated_data["content"],
        )

        return Response(
            MessageSerializer(result.assistant_message).data,
            status=status.HTTP_201_CREATED,
        )
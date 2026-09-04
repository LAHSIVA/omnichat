from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ConversationMessageStreamView
from .views import (
    ConversationMessageListCreateView,
    ConversationViewSet,
)


router = DefaultRouter()

router.register(
    "conversations",
    ConversationViewSet,
    basename="conversation",
)


urlpatterns = router.urls + [
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessageListCreateView.as_view(),
        name="conversation-messages",
    ),

    path(
        "conversations/<uuid:conversation_id>/messages/stream/",
        ConversationMessageStreamView.as_view(),
        name="conversation-message-stream",
    ),
]
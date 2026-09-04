from django.urls import path

from knowledge.views import (
    DocumentDetailView,
    DocumentListCreateView,
    DocumentRetryView,
)


urlpatterns = [
    path(
        "documents/",
        DocumentListCreateView.as_view(),
        name="document-list-create",
    ),
    path(
        "documents/<int:pk>/",
        DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "documents/<int:pk>/retry/",
        DocumentRetryView.as_view(),
        name="document-retry",
    ),
]
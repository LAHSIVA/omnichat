from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .serializers import HealthResponseSerializer


class HealthCheckView(APIView):
    """Return the application's liveness status."""

    permission_classes = [AllowAny]

    @extend_schema(responses=HealthResponseSerializer)
    def get(self, request):
        """Return a successful health response."""
        return Response({"status": "ok"})
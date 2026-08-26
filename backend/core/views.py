from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Return the application's liveness status."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Return a successful health response."""
        return Response({"status": "ok"})
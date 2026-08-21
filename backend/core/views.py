from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Return the application's liveness status."""

    def get(self, request):
        """Return a successful health response."""
        return Response({"status": "ok"})
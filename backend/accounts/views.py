from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegistrationSerializer


class RegistrationView(generics.CreateAPIView):
    """Create a new user account."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    """Return the currently authenticated user."""

    def get(self, request):
        """Return basic information about the authenticated user."""
        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            }
        )
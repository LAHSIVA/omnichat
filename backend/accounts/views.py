from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer, RegistrationSerializer


class RegistrationView(generics.CreateAPIView):
    """Create a new user account."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class CurrentUserView(generics.RetrieveAPIView):
    """Return the currently authenticated user."""

    serializer_class = CurrentUserSerializer

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user
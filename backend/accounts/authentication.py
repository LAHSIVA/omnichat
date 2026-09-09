from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import CurrentUserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add the authenticated user's profile to the JWT response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = CurrentUserSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Return JWT tokens together with the authenticated user."""

    serializer_class = CustomTokenObtainPairSerializer

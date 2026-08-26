from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new user account."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        """Create a user using Django's password hashing."""
        return User.objects.create_user(**validated_data)
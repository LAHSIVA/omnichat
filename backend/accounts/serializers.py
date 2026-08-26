from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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

    def validate_password(self, value):
        """Validate the password against Django's password validators."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Create the user using Django's password hashing."""
        return User.objects.create_user(**validated_data)


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serialize the currently authenticated user."""

    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = ("id", "username", "email")
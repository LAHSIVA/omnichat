from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer):
    """Serialize the application health response."""

    status = serializers.CharField()
from rest_framework import serializers
from .models import Service, ServiceCredential


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "code", "name", "description")


class ServiceCredentialSerializer(serializers.ModelSerializer):
    value = serializers.CharField(read_only=True)

    class Meta:
        model = ServiceCredential
        fields = ["id", "key", "value", "is_secret"]

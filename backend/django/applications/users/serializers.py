from .models import User
from rest_framework import serializers
from accounts.serializers import AccountSerializer


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # Usa create_user para asegurar hashing de contraseña
        return User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id")
    accounts = AccountSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["user_id", "accounts"]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email"]

    email = serializers.EmailField()


class ScanningSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()

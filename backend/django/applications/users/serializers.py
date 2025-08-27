from .models import User
from rest_framework import serializers
from accounts.serializers import AccountSerializer, AccountSerializerBackend


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # Usa create_user para asegurar hashing de contraseña
        return User.objects.create_user(**validated_data)


class UserAccountSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id")
    user = serializers.CharField(source="name")
    user_email = serializers.EmailField(source="email")
    accounts = AccountSerializer(many=True, read_only=True)
    total_invoices_user = serializers.IntegerField(source="total_invoices_scanned")

    class Meta:
        model = User
        fields = [
            "user_id",
            "user",
            "user_email",
            "total_invoices_user",
            "accounts",
        ]


class UserAccountSerializerBackend(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id")
    accounts = AccountSerializerBackend(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "user_id",
            "accounts",
        ]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email"]

    email = serializers.EmailField()


class ScanningSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    account_id = serializers.IntegerField()

# applications\users\serializers.py
from .models import User

from rest_framework import serializers
from rest_framework.exceptions import NotFound


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "is_active",
            "date_joined",
            "total_invoices_scanned",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "name", "is_active", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserWithAccountSerializer(UserSerializer):
    account_id = serializers.SerializerMethodField()
    account_name = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["account_id", "account_name"]

    def _get_account_info(self):
        account_info = self.context.get("account_info")
        if not account_info:
            raise NotFound("El usuario no existe o no tiene cuenta asociada.")
        return account_info

    def get_account_id(self, obj):
        return self._get_account_info().get("id")

    def get_account_name(self, obj):
        return self._get_account_info().get("name")

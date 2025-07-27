from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(source="id")
    account_name = serializers.CharField(source="name")
    account_tax_id = serializers.CharField(source="tax_id")

    class Meta:
        model = Account
        fields = ["account_id", "account_name", "account_tax_id"]

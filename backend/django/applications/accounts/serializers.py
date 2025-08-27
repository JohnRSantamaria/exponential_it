from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(source="id")
    account_name = serializers.CharField(source="name")
    account_tax_id = serializers.CharField(source="tax_id")
    total_invoices_account = serializers.IntegerField(source="total_invoices_scanned")

    class Meta:
        model = Account
        fields = [
            "account_id",
            "account_name",
            "account_tax_id",
            "total_invoices_account",
        ]


class AccountSerializerBackend(serializers.ModelSerializer):
    account_id = serializers.IntegerField(source="id")
    account_name = serializers.CharField(source="name")
    account_tax_id = serializers.CharField(source="tax_id")

    class Meta:
        model = Account
        fields = [
            "account_id",
            "account_name",
            "account_tax_id",
        ]

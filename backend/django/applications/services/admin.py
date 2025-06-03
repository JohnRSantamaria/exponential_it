# applications/services/admin.py

from django.contrib import admin

from services.forms import ServiceCredentialForm
from .models import AccountService, Service, ServiceCredential


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(AccountService)
class AccountServiceAdmin(admin.ModelAdmin):
    list_display = ("account", "service", "is_active", "date_subscribed")
    list_filter = ("is_active", "service")
    search_fields = ("account__name",)


@admin.register(ServiceCredential)
class ServiceCredentialAdmin(admin.ModelAdmin):
    form = ServiceCredentialForm
    list_display = (
        "account_service",
        "key",
        "display_value",
        "is_secret",
        "created",
        "updated",
    )
    readonly_fields = ("created", "updated")

    def display_value(self, obj):
        return "-" if obj.is_secret else obj.value

    display_value.short_description = "Value"

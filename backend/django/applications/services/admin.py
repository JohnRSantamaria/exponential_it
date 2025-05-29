# applications/services/admin.py

from django.contrib import admin
from .models import Service, UserService, ServiceCredential
from .forms import ServiceCredentialForm


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(UserService)
class UserServiceAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "is_active", "date_subscribed")
    list_filter = ("is_active", "service")
    search_fields = ("user__email",)


@admin.register(ServiceCredential)
class ServiceCredentialAdmin(admin.ModelAdmin):
    form = ServiceCredentialForm
    list_display = (
        "user_service",
        "key",
        "display_value",
        "is_secret",
        "created",
        "updated",
    )
    readonly_fields = ("created", "updated")
    search_fields = ("user_service__user__email", "key")

    def display_value(self, obj):
        return "-" if obj.is_secret else obj.value

    display_value.short_description = "Value"

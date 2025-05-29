from django.contrib import admin

from .forms import CampAdminForm
from .models import Camp


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    form = CampAdminForm

    list_display = (
        "name",
        "db_name",
        "db_user",
        "db_host",
        "db_port",
        "active",
        "created",
        "updated",
    )
    search_fields = ("name", "db_name", "db_user")
    list_filter = ("active", "db_host")
    readonly_fields = ("created", "updated")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "db_name",
                    "db_user",
                    "db_password",
                    "db_host",
                    "db_port",
                    "active",
                    "created",
                    "updated",
                )
            },
        ),
    )

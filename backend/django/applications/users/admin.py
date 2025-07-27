from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "name",
        "is_active",
        "date_joined",
        "total_invoices_scanned",
    ]
    search_fields = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("name",)}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas", {"fields": ("date_joined", "last_login")}),
        ("Facturas escaneadas", {"fields": ("total_invoices_scanned",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2"),
            },
        ),
    )
    readonly_fields = [
        "date_joined",
        "last_login",
        "total_invoices_scanned",
        "maximum_scanned_invoices",
    ]


admin.site.register(User, UserAdmin)

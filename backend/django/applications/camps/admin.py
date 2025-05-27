from django.contrib import admin
from django import forms
from .models import Camp


class CampAdminForm(forms.ModelForm):
    db_password = forms.CharField(
        label="Contraseña de la base de datos",
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text="Se cifrará automáticamente",
    )

    class Meta:
        model = Camp
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["db_password"] = self.instance.db_password

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("db_password"):
            instance.db_password = self.cleaned_data["db_password"]
        if commit:
            instance.save()
        return instance


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
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "db_name", "db_user")
    list_filter = ("active", "db_host")
    readonly_fields = ("created_at", "updated_at")

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
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    

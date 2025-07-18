from django.contrib import admin
from django import forms
from .models import Account
from .forms import AccountAdminForm


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    form = AccountAdminForm
    list_display = ("name", "user", "tax_id", "total_invoices_scanned")
    search_fields = ("name", "user__email")
    readonly_fields = ("total_invoices_scanned", "created")
    list_filter = ("user",)  # ✅ Activa filtro lateral por usuario

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Oculta el campo `user` pero lo deja funcional
            form.base_fields["user"].initial = request.user
            form.base_fields["user"].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.user != request.user:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.user != request.user:
            return False
        return super().has_delete_permission(request, obj)

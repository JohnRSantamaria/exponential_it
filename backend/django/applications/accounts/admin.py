# applications/accounts/admin.py
from django.contrib import admin
from .models import Account
from .forms import AccountAdminForm


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    form = AccountAdminForm
    list_display = ("name", "user", "created")
    search_fields = ("name", "user__email")

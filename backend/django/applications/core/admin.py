# core/admin.py (o en cualquier admin mixin)
from django.contrib import admin
from django.db import connections
from applications.core.db_context import get_current_camp


class MultiDBAdminMixin:
    def get_queryset(self, request):
        camp = get_current_camp()
        db = camp.db_name if camp else "default"
        return super().get_queryset(request).using(db)

    def save_model(self, request, obj, form, change):
        camp = get_current_camp()
        db = camp.db_name if camp else "default"
        obj.save(using=db)

    def delete_model(self, request, obj):
        camp = get_current_camp()
        db = camp.db_name if camp else "default"
        obj.delete(using=db)

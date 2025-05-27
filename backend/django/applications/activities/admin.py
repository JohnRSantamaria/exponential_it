# applications/activities/admin.py
from django.contrib import admin
from .models import Activity, SKill, ActivitySkill


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "duration", "required_monitors")
    search_fields = ("name",)
    list_filter = ("required_monitors",)
    ordering = ("name",)


@admin.register(SKill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ActivitySkill)
class ActivitySkillAdmin(admin.ModelAdmin):
    list_display = ("activity", "skill")
    list_filter = ("activity", "skill")
    search_fields = ("activity__name", "skill__name")
    ordering = ("activity__name", "skill__name")

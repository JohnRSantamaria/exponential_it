from django.contrib import admin
from .models import Schedule, Day, ScheduledActivity


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    list_filter = ("start_date", "end_date")
    search_fields = ("name",)
    ordering = ("start_date",)


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ("schedule", "date")
    list_filter = ("schedule", "date")
    search_fields = ("schedule__name",)
    ordering = ("date", "schedule")


@admin.register(ScheduledActivity)
class ScheduledActivityAdmin(admin.ModelAdmin):
    list_display = (
        "get_schedule",
        "get_date",
        "start_time",
        "end_time",
        "get_activity_name",
    )
    list_filter = ("day__schedule", "day__date", "activity")
    search_fields = ("day__schedule__name", "day__date", "activity__name")
    ordering = ("day__date", "start_time")

    def get_schedule(self, obj):
        return obj.day.schedule.name

    get_schedule.short_description = "Schedule"

    def get_date(self, obj):
        return obj.day.date

    get_date.short_description = "Date"

    def get_activity_name(self, obj):
        return obj.activity.name

    get_activity_name.short_description = "Activity"

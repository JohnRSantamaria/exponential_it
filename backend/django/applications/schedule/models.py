# applications\schedule\models.py
from datetime import datetime, timedelta
from django.db import models
from activities.models import Activity


class Schedule(models.Model):
    """Model representing a block of time in a schedule. ie. a week or a month."""

    name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name}: desde ({self.start_date} hasta {self.end_date})"

    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        ordering = ["start_date"]


class Day(models.Model):
    """Model representing a day in a schedule."""

    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="days"
    )
    date = models.DateField()

    def __str__(self):
        return f"{self.schedule.name} - {self.date}"

    class Meta:
        verbose_name = "Day"
        verbose_name_plural = "Days"
        ordering = ["date"]
        unique_together = ("schedule", "date")


class ScheduledActivity(models.Model):
    """Model representing an activity scheduled using  start_time."""

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="scheduled_activities",
    )

    day = models.ForeignKey(
        Day, on_delete=models.CASCADE, related_name="scheduled_activities"
    )
    start_time = models.TimeField()

    @property
    def end_time(self):
        start_dt = datetime(2000, 1, 1, self.start_time.hour, self.start_time.minute)
        return (start_dt + timedelta(minutes=self.activity.duration)).time()

    def __str__(self):
        return f"{self.day.schedule.name} - {self.day.date} - {self.start_time}"

    class Meta:
        verbose_name = "Scheduled Activity"
        verbose_name_plural = "Scheduled Activities"
        ordering = ["day", "start_time"]
        unique_together = ("day", "start_time")

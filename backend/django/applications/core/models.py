# core/models.py
from django.db import models

from applications.core.constants import GROUP_CHOICES


class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating 'creation_date' and 'update_date' fields.
    """

    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    update_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ["-creation_date"]
        verbose_name = "Time Stamped Model"
        verbose_name_plural = "Time Stamped Models"


class Group(models.Model):
    """
    Model representing a group of activities.
    """

    id = models.CharField(primary_key=True, max_length=1, choices=GROUP_CHOICES)
    description = models.TextField()
    min_age = models.PositiveIntegerField()
    max_age = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.get_id_display()} ({self.min_age}-{self.max_age})"

# applications\activities\models.py
from datetime import datetime, timedelta
from django.db import models


class Activity(models.Model):
    """Actividad general con duracion y requerimientos."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duración en minutos")
    required_monitors = models.PositiveIntegerField(
        default=1, help_text="Número de monitores requeridos para la actividad"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ["name"]


class SKill(models.Model):
    """Habilidades requeridas para una actividad."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Habilidad"
        verbose_name_plural = "Habilidades"
        ordering = ["name"]


class ActivitySkill(models.Model):
    """Relación entre actividades y habilidades requeridas."""

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="skills"
    )
    skill = models.ForeignKey(
        SKill, on_delete=models.CASCADE, related_name="activities"
    )

    def __str__(self):
        return f"{self.activity.name} - {self.skill.name}"

    class Meta:
        verbose_name = "Actividad-Habilidad"
        verbose_name_plural = "Actividades-Habilidades"
        unique_together = ("activity", "skill")
        ordering = ["activity__name", "skill__name"]

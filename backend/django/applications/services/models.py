from django.db import models
from django.utils import timezone

from users.models import User


class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserService(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_services"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "service")

    def __str__(self):
        return f"{self.user.email} - {self.service.code}"

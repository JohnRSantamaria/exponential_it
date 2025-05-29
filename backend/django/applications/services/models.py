from django.db import models
from django.utils import timezone


from applications.core.log_utils import decrypt_value, encrypt_value
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


class ServiceCredential(models.Model):
    user_service = models.ForeignKey(
        "UserService", on_delete=models.CASCADE, related_name="credentials"
    )
    key = models.CharField(max_length=100)
    _value = models.BinaryField(db_column="value")
    is_secret = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def value(self):
        if self.is_secret:
            return decrypt_value(self._value)
        return self._value.decode()

    @value.setter
    def value(self, val: str):
        self._value = encrypt_value(val) if self.is_secret else val.encode()

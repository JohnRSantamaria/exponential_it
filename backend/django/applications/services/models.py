# applications\services\models.py
from django.db import models
from django.utils import timezone


from accounts.models import Account
from core.log_utils import decrypt_value, encrypt_value


class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class AccountService(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_services"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("account", "service")

    def __str__(self):
        return f"{self.service.name} | {self.account.name}"


class ServiceCredential(models.Model):

    account_service = models.ForeignKey(
        AccountService, on_delete=models.CASCADE, related_name="credentials"
    )
    key = models.CharField(max_length=100)
    _value = models.BinaryField(db_column="value")
    is_secret = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def value(self):
        raw = self._value
        if isinstance(raw, memoryview):
            raw = raw.tobytes()

        if self.is_secret:
            return decrypt_value(raw)
        return raw.decode()

    @value.setter
    def value(self, val: str):
        self._value = encrypt_value(val) if self.is_secret else val.encode()

    class Meta:
        unique_together = ("account_service", "key")

    def __str__(self):
        return f"{self.account_service} : {self.key}"

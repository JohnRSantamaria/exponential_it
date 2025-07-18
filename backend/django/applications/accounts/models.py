# applications/accounts/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from applications.accounts.validators import validate_tax_id
from users.models import User


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=100, help_text="Nombre de la cuenta")
    tax_id = models.CharField(
        help_text="Identificacion fiscal",
        max_length=20,
        validators=[validate_tax_id],
        unique=True,
    )
    created = models.DateTimeField(default=timezone.now)
    total_invoices_scanned = models.PositiveIntegerField(default=0)

    def clean(self):

        normalized_name = "_".join(self.name.lower().strip().split())
        qs = Account.objects.filter(user=self.user, name=normalized_name)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                f"Ya existe una cuenta con el nombre: '{self.name}' para este usuario.'{normalized_name}'"
            )

    def save(self, *args, **kwargs):
        if self.name:
            self.name = "_".join(self.name.lower().strip().split())
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    class Meta:
        unique_together = ("user", "name")

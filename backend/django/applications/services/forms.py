# applications/services/forms.py

from django import forms
from .models import ServiceCredential


class ServiceCredentialForm(forms.ModelForm):
    value = forms.CharField(
        required=False,
        label="Value",
        widget=forms.PasswordInput(render_value=False),
        help_text="Introduce un nuevo valor solo si deseas reemplazar el actual.",
    )

    class Meta:
        model = ServiceCredential
        fields = ["user_service", "key", "is_secret", "value"]

    def save(self, commit=True):
        instance: ServiceCredential = super().save(commit=False)

        new_value = self.cleaned_data.get("value")
        if new_value:  # Solo sobrescribe si hay uno nuevo
            instance.value = new_value

        if commit:
            instance.save()
        return instance

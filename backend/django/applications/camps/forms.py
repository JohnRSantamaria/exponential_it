from django import forms

from .models import Camp


class CampAdminForm(forms.ModelForm):
    db_password = forms.CharField(
        label="Contraseña db",
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text="Introduce un nuevo valor solo si deseas reemplazar el actual.",
    )

    class Meta:
        model = Camp
        fields = "__all__"

    def save(self, commit=True):
        instance: Camp = super().save(commit=False)

        new_value = self.cleaned_data.get("value")
        if new_value:  # Solo sobrescribe si hay uno nuevo
            instance.value = new_value

        if commit:
            instance.save()
        return instance

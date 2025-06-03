from django import forms
from .models import Account


class AccountAdminForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = "__all__"

    def clean_name(self):
        # Limpia espacios y reemplaza por "_"
        name = self.cleaned_data.get("name", "").strip()
        return "_".join(name.split())

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        name = cleaned_data.get("name")

        if user and name:
            qs = Account.objects.filter(user=user, name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Ya existe una cuenta con ese nombre para el usuario {user.email}"
                )

        return cleaned_data

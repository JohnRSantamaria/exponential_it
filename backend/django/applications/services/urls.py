# applications/accounts/urls.py
from django.urls import path


from .views import ServicesAccounts

urlpatterns = [
    path("", ServicesAccounts.as_view(), name="accounts"),
]

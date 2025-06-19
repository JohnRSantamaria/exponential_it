# applications\services\urls.py
from django.urls import path
from .views import (
    ServiceCredentialsByServiceIdView,
    ServicesAccountsView,
    ServiceCredentialsView,
)

urlpatterns = [
    path("", ServicesAccountsView.as_view(), name="accounts"),
    path("credentials/", ServiceCredentialsView.as_view(), name="service-credentials"),
    path(
        "<int:service_id>/credentials/",
        ServiceCredentialsByServiceIdView.as_view(),
        name="service-credentials-by-id",
    ),
]

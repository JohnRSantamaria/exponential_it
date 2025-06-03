# applications/accounts/urls.py
from django.urls import path

from accounts.views import IsServiceActiveView, UserAccountsView

urlpatterns = [
    path("", UserAccountsView.as_view(), name="accounts"),
    path(
        "is-service-active/<int:account_id>/<int:service_id>/",
        IsServiceActiveView.as_view(),
        name="is-service-active",
    ),
]

# applications/services/api/urls.py

from django.urls import path
from .views import ActiveServiceCredentialsView

urlpatterns = [
    path("<str:service_code>/", ActiveServiceCredentialsView.as_view()),
]

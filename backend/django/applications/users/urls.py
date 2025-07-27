from django.urls import path
from users.views import RegisterUserView, ScanningView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("scanning/", ScanningView.as_view(), name="scanning"),
]

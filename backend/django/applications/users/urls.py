# applications\users\urls.py
from django.urls import path
from .views import (
    RegisterUserView,
    LoginView,
    UserServicesView,
    RefreshTokenView,
    LogoutView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("services/", UserServicesView.as_view(), name="user-services"),
    path("logout/", LogoutView.as_view(), name="logout-session"),
]

# applications\users\urls.py
from django.urls import path
from .views import (
    IdentifyUserAccountsView,
    MeView,
    RegisterUserView,
    LoginView,
    RefreshTokenView,
    LogoutView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout-session"),
    path("me/", MeView.as_view(), name="user-me"),
    path(
        "identify/", IdentifyUserAccountsView.as_view(), name="identify-user-accounts"
    ),
]

from django.urls import path
from users.views import LoginView, LogoutView, RefreshTokenView, MeView, IdentifyView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh"),
    path("identify/", IdentifyView.as_view(), name="identify"),
]

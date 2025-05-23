# applications\users\urls.py
from django.urls import path
from .views import RegisterUserView, CustomTokenView, UserServicesView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("token/", CustomTokenView.as_view(), name="token"),
    path("services/", UserServicesView.as_view(), name="user-services"),    
]

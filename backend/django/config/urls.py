from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/users/", include("users.urls")),
    path("secret/", include("services.urls")),
    # path("campers/", include("applications.schedule.urls")),
]

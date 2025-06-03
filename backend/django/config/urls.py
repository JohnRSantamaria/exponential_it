from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/users/", include("users.urls")),    
    path("accounts/", include("accounts.urls")),
    path("services/", include("services.urls")),
    # path("campers/", include("applications.schedule.urls")),
]


handler404 = "core.exception_handler.custom_handler404"
handler500 = "core.exception_handler.custom_handler500"

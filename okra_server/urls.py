from django.contrib import admin
from django.urls import include, path

from okra_server import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login", admin.site.login),
    path("logout", admin.site.logout),
    path("registration_details/<participant_id>", views.registration_details),
    path("api/", include("okra_server.api.urls")),
]

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from okra_server import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login", admin.site.login, name="login"),
    path("logout", admin.site.logout, name="logout"),
    path("", views.index),
    path(
        "registration/<participant_id>",
        views.registration_detail,
        name="registration-detail",
    ),
    path(
        "experiments",
        login_required(views.ExperimentList.as_view()),
        name="experiment-list",
    ),
    path(
        "experiments/new",
        login_required(views.ExperimentDetail.as_view()),
        name="experiment-new",
    ),
    path(
        "experiments/<uuid:experiment_id>",
        login_required(views.ExperimentDetail.as_view()),
        name="experiment-detail",
    ),
    path(
        "experiments/<uuid:experiment_id>/results",
        login_required(views.experiment_results),
        name="experiment-results",
    ),
    path(
        "participants",
        login_required(views.ParticipantList.as_view()),
        name="participant-list",
    ),
    path(
        "participants/new",
        login_required(views.new_participant),
        name="participant-new",
    ),
    path("api/", include("okra_server.api.urls")),
]

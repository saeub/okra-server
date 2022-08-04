from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import include, path

from okra_server import views


def superuser_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login", views.Login.as_view(), name="login"),
    path("logout", views.logout, name="logout"),
    path("", views.index),
    path(
        "registration/<participant_id>",
        views.registration_detail,
        name="registration-detail",
    ),
    path(
        "experiments",
        superuser_required(views.ExperimentList.as_view()),
        name="experiment-list",
    ),
    path(
        "experiments/new",
        superuser_required(views.ExperimentDetail.as_view()),
        name="experiment-new",
    ),
    path(
        "experiments/<uuid:experiment_id>",
        superuser_required(views.ExperimentDetail.as_view()),
        name="experiment-detail",
    ),
    path(
        "experiments/<uuid:experiment_id>/results",
        superuser_required(views.experiment_results),
        name="experiment-results",
    ),
    path(
        "participants",
        login_required(views.ParticipantList.as_view()),
        name="participant-list",
    ),
    path(
        "participants/new",
        superuser_required(views.new_participant),
        name="participant-new",
    ),
    path("api/", include("okra_server.api.urls")),
]

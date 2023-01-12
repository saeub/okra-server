from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import include, path

from okra_server import views


def staff_required(function):
    return user_passes_test(
        lambda u: u.is_staff,
    )(function)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login", views.Login.as_view(), name="login"),
    path("logout", views.logout, name="logout"),
    path("", views.index, name="index"),
    path(
        "registration/<participant_id>",
        views.registration_detail,
        name="registration-detail",
    ),
    path(
        "experiments",
        staff_required(views.ExperimentList.as_view()),
        name="experiment-list",
    ),
    path(
        "experiments/new",
        staff_required(views.ExperimentDetail.as_view()),
        name="experiment-new",
    ),
    path(
        "experiments/<uuid:experiment_id>",
        staff_required(views.ExperimentDetail.as_view()),
        name="experiment-detail",
    ),
    path(
        "experiments/<uuid:experiment_id>/results",
        staff_required(views.experiment_results),
        name="experiment-results",
    ),
    path(
        "experiments/<uuid:experiment_id>/results/<uuid:participant_id>/graph",
        staff_required(views.experiment_results_graph),
        name="experiment-results-graph",
    ),
    path(
        "experiments/<uuid:experiment_id>/delete",
        staff_required(views.delete_experiment),
        name="experiment-delete",
    ),
    path(
        "participants",
        login_required(views.ParticipantList.as_view()),
        name="participant-list",
    ),
    path(
        "participants/new",
        staff_required(views.new_participant),
        name="participant-new",
    ),
    path(
        "participants/<uuid:participant_id>/label",
        staff_required(views.label_participant),
        name="participant-label",
    ),
    path(
        "participants/<uuid:participant_id>/unregister",
        staff_required(views.unregister_participant),
        name="participant-unregister",
    ),
    path(
        "participants/<uuid:participant_id>/delete",
        staff_required(views.delete_participant),
        name="participant-delete",
    ),
    path("api/", include("okra_server.api.urls")),
]

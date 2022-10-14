from django.urls import path

from okra_server.api import views

app_name = "api"
urlpatterns = [
    path("", views.base, name="base"),
    path("register", views.register),
    path("experiments", views.get_experiments),
    path("experiments/<experiment_id>", views.get_experiment),
    path("experiments/<experiment_id>/start", views.start_task),
    path("tasks/<task_id>/finish", views.finish_task),
]

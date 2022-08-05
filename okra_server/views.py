import base64
import io
import json
import uuid

import qrcode
from django.contrib import auth
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, View

from okra_server import models


def index(request):
    participants = models.Participant.objects.all()
    experiments_data = []
    for experiment in models.Experiment.objects.all():
        participants_data = []
        for participant in participants:
            n_tasks = experiment.get_n_tasks(participant)
            n_tasks_unfinished = experiment.get_n_tasks_done(
                participant, finished=False, canceled=False
            )
            n_tasks_finished = experiment.get_n_tasks_done(
                participant, finished=True, canceled=False
            )
            n_tasks_canceled = experiment.get_n_tasks_done(
                participant, finished=True, canceled=True
            )
            participants_data.append(
                {
                    "id": str(participant.id),
                    "n_practice_tasks_finished": experiment.get_n_tasks_done(
                        participant, practice=True, finished=True, canceled=False
                    ),
                    "n_tasks": n_tasks,
                    "n_tasks_unfinished": n_tasks_unfinished,
                    "percent_tasks_unfinished": n_tasks_unfinished
                    / (n_tasks or 1)
                    * 100,
                    "n_tasks_finished": n_tasks_finished,
                    "percent_tasks_finished": n_tasks_finished / (n_tasks or 1) * 100,
                    "n_tasks_canceled": n_tasks_canceled,
                    "percent_tasks_canceled": n_tasks_canceled / (n_tasks or 1) * 100,
                }
            )
        experiments_data.append(
            {
                "id": str(experiment.id),
                "title": experiment.title,
                "task_type": dict(models.TaskType.choices)[experiment.task_type],
                "participants": participants_data,
            }
        )
    return render(
        request,
        "okra_server/index.html",
        {"experiments": experiments_data},
    )


def registration_detail(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    if participant.device_key is not None:
        return HttpResponse("already registered", status=404)

    base_url = request.build_absolute_uri("/api")
    data = f"{base_url}\n" f"{participant.id}\n" f"{participant.registration_key}"
    image = qrcode.make(data)
    image_bytes = io.BytesIO()
    image.save(image_bytes, "PNG")
    image_base64 = base64.b64encode(image_bytes.getvalue())

    return render(
        request,
        "okra_server/registration_detail.html",
        {
            "base_url": base_url,
            "participant_id": participant.id,
            "registration_key": participant.registration_key,
            "qr_data": image_base64.decode("ascii"),
        },
    )


class ExperimentList(ListView):
    model = models.Experiment


class ExperimentDetail(View):
    def get(self, request, experiment_id=None):
        experiment = self._get_experiment(experiment_id)
        return render(
            request,
            "okra_server/experiment_detail.html",
            {
                "data": {
                    "id": str(experiment.id),
                    "taskType": experiment.task_type,
                    "title": experiment.title,
                    "instructions": experiment.instructions,
                    "practiceTask": (
                        {
                            "id": str(experiment.practice_task.id),
                            "label": experiment.practice_task.label,
                            "data": experiment.practice_task.data,
                            "instructionsAfter": (
                                experiment.practice_task.instructions_after
                            ),
                        }
                        if experiment.practice_task is not None
                        else None
                    ),
                    "tasks": [
                        {
                            "id": str(task.id),
                            "label": task.label,
                            "data": task.data,
                            "instructionsAfter": task.instructions_after,
                        }
                        for task in experiment.tasks.all()
                    ],
                    "ratings": [
                        {
                            "id": str(rating.id),
                            "question": rating.question,
                            "type": rating.rating_type,
                            "lowExtreme": rating.low_extreme,
                            "highExtreme": rating.high_extreme,
                        }
                        for rating in experiment.ratings.all()
                    ],
                    "assignments": [
                        {
                            "participant": str(participant.id),
                            "tasks": [
                                {
                                    "id": str(assignment.task.id),
                                    "started": assignment.started_time is not None,
                                }
                                for assignment in experiment.get_assignments(
                                    participant
                                )
                            ],
                        }
                        for participant in models.Participant.objects.all()
                    ],
                },
                "task_type_choices": {
                    type_id: type_name for type_id, type_name in models.TaskType.choices
                },
                "rating_type_choices": {
                    type_id: type_name
                    for type_id, type_name in models.TaskRatingType.choices
                },
            },
        )

    def post(self, request, experiment_id=None):
        experiment = self._get_experiment(experiment_id)
        data = json.loads(request.body)

        experiment.task_type = data["taskType"]
        experiment.title = data["title"]
        experiment.instructions = data["instructions"]

        practice_task_data = data["practiceTask"]
        if experiment.practice_task is not None and (
            practice_task_data is None
            or experiment.practice_task.id != uuid.UUID(practice_task_data["id"])
        ):
            experiment.practice_task.delete()
            experiment.practice_task = None
        if practice_task_data is not None:
            experiment.practice_task = self._get_task(practice_task_data["id"])
            experiment.practice_task.label = practice_task_data["label"]
            experiment.practice_task.data = practice_task_data["data"]
            experiment.practice_task.instructions_after = practice_task_data[
                "instructionsAfter"
            ]
            experiment.practice_task.save()

        experiment.save()

        tasks_to_delete = set(experiment.tasks.all())
        for task_data in data["tasks"]:
            task = self._get_task(task_data["id"])
            if task in tasks_to_delete:
                tasks_to_delete.remove(task)
            task.experiment = experiment
            task.label = task_data["label"]
            task.data = task_data["data"]
            task.instructions_after = task_data["instructionsAfter"]
            task.save()
        for task in tasks_to_delete:
            task.delete()

        for assignment_data in data["assignments"]:
            participant = models.Participant.objects.get(
                id=assignment_data["participant"]
            )
            experiment.get_assignments(participant).filter(
                started_time__isnull=True
            ).delete()
            for task_data in assignment_data["tasks"]:
                if task_data["started"]:
                    continue
                models.TaskAssignment.objects.create(
                    participant=participant,
                    task_id=task_data["id"],
                )

        experiment.ratings.all().delete()
        for rating_data in data["ratings"]:
            rating = self._get_rating(rating_data["id"])
            rating.experiment = experiment
            rating.question = rating_data["question"]
            rating.rating_type = rating_data["type"]
            rating.low_extreme = rating_data["lowExtreme"]
            rating.high_extreme = rating_data["highExtreme"]
            rating.save()

        return JsonResponse(
            {
                "message": "Saved",
                "redirect": reverse(
                    "experiment-detail", kwargs={"experiment_id": experiment.id}
                ),
            },
            status=200,
        )

    @staticmethod
    def _get_experiment(experiment_id) -> models.Experiment:
        if experiment_id is not None:
            return models.Experiment.objects.get(id=experiment_id)
        else:
            return models.Experiment()

    @staticmethod
    def _get_task(task_id) -> models.Task:
        try:
            return models.Task.objects.get(id=task_id)
        except models.Task.DoesNotExist:
            return models.Task(id=task_id)

    @staticmethod
    def _get_rating(rating_id) -> models.TaskRating:
        try:
            return models.TaskRating.objects.get(id=rating_id)
        except models.TaskRating.DoesNotExist:
            return models.TaskRating(id=rating_id)


def experiment_results(request, experiment_id):
    download = "download" in request.GET
    experiment = models.Experiment.objects.get(id=experiment_id)
    results = {
        "results": [
            {
                "participant": participant.id,
                "practiceTasks": [
                    {
                        "task": assignment.task.id,
                        "results": assignment.results,
                        "started_time": assignment.started_time,
                        "finished_time": assignment.finished_time,
                    }
                    for assignment in experiment.get_assignments(
                        participant, practice=True
                    )
                ],
                "tasks": [
                    {
                        "task": assignment.task.id,
                        "results": assignment.results,
                        "started_time": assignment.started_time,
                        "finished_time": assignment.finished_time,
                    }
                    for assignment in experiment.get_assignments(participant)
                ],
            }
            for participant in models.Participant.objects.all()
        ],
    }
    response = JsonResponse(
        results,
        status=200,
    )
    if download:
        response["Content-Disposition"] = f"attachment; filename={experiment.id}.json"
    return response


class ParticipantList(ListView):
    model = models.Participant


@require_POST
def new_participant(request):
    models.Participant.objects.create()
    return redirect("participant-list")


class Login(View):
    def get(self, request):
        return render(request, "okra_server/login.html")

    def post(self, request):
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect(request.GET.get("next") or index)
        else:
            return render(
                request,
                "okra_server/login.html",
                {"username": username, "failed": True},
            )


def logout(request):
    auth.logout(request)
    return redirect(request.GET.get("next") or index)

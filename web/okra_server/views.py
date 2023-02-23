import base64
import io
import itertools
import json
import random
import uuid
from datetime import datetime

import qrcode
from django.conf import settings
from django.contrib import auth
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, View

from okra_server import models


def api_info(request):
    return {"api_info": settings.API_INFO}


def index(request):
    experiments_data = [
        {
            "id": str(experiment.id),
            "title": experiment.title,
            "task_type": dict(models.TaskType.choices)[experiment.task_type],
        }
        for experiment in models.Experiment.objects.all()
    ]
    return render(
        request,
        "okra_server/index.html",
        {"experiments": experiments_data},
    )


def progress(request, experiment_id):
    participants = models.Participant.objects.all()
    participants_data = []
    experiment = models.Experiment.objects.get(id=experiment_id)
    for participant in participants:
        n_tasks = experiment.get_n_tasks(participant)
        n_tasks_unfinished = experiment.get_n_tasks(
            participant, started=True, finished=False, canceled=False
        )
        n_tasks_finished = experiment.get_n_tasks(
            participant, started=True, finished=True, canceled=False
        )
        n_tasks_canceled = experiment.get_n_tasks(
            participant, started=True, finished=True, canceled=True
        )
        participants_data.append(
            {
                "id": str(participant.id),
                "label": participant.label,
                "n_practice_tasks_finished": experiment.get_n_tasks(
                    participant, practice=True, finished=True, canceled=False
                ),
                "n_tasks": n_tasks,
                "n_tasks_unfinished": n_tasks_unfinished,
                "percent_tasks_unfinished": n_tasks_unfinished / (n_tasks or 1) * 100,
                "n_tasks_finished": n_tasks_finished,
                "percent_tasks_finished": n_tasks_finished / (n_tasks or 1) * 100,
                "n_tasks_canceled": n_tasks_canceled,
                "percent_tasks_canceled": n_tasks_canceled / (n_tasks or 1) * 100,
            }
        )
    return render(
        request,
        "okra_server/progress.html",
        {
            "experiment": {
                "id": str(experiment.id),
                "title": experiment.title,
                "task_type": dict(models.TaskType.choices)[experiment.task_type],
            },
            "participants": participants_data,
        },
    )


def registration_detail(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    if participant.device_key is not None:
        return HttpResponse("already registered", status=404)

    base_url = request.build_absolute_uri(reverse("api:base")).rstrip("/")
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
                    "instructionsAfterTask": experiment.instructions_after_task,
                    "instructionsAfterPracticeTask": (
                        experiment.instructions_after_practice_task
                    ),
                    "instructionsAfterFinalTask": (
                        experiment.instructions_after_final_task
                    ),
                    "practiceTask": (
                        {
                            "id": str(experiment.practice_task.id),
                            "label": experiment.practice_task.label,
                            "data": experiment.practice_task.data,
                        }
                        if experiment.practice_task is not None
                        else None
                    ),
                    "tasks": [
                        {
                            "id": str(task.id),
                            "label": task.label,
                            "data": task.data,
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
                    "requirements": [
                        str(required_experiment.id)
                        for required_experiment in experiment.required_experiments.all()
                        if required_experiment != experiment
                    ],
                    "assignments": {
                        str(participant.id): [
                            {
                                "id": str(assignment.task.id),
                                "started": assignment.started_time is not None,
                            }
                            for assignment in experiment.get_assignments(participant)
                        ]
                        for participant in models.Participant.objects.all()
                    },
                },
                "task_type_choices": {
                    type_id: type_name for type_id, type_name in models.TaskType.choices
                },
                "rating_type_choices": {
                    type_id: type_name
                    for type_id, type_name in models.TaskRatingType.choices
                },
                "experiment_titles": {
                    str(experiment.id): experiment.title
                    for experiment in models.Experiment.objects.all()
                },
                "participant_labels": {
                    str(participant.id): participant.label
                    for participant in models.Participant.objects.all()
                },
            },
        )

    def post(self, request, experiment_id=None):
        data = json.loads(request.body)
        experiment_id = experiment_id or data.get("id")
        experiment = self._get_experiment(experiment_id)

        try:
            experiment.task_type = data["taskType"]
            experiment.title = data["title"]
            experiment.instructions = data["instructions"]
            experiment.instructions_after_task = data["instructionsAfterTask"]
            experiment.instructions_after_practice_task = data[
                "instructionsAfterPracticeTask"
            ]
            experiment.instructions_after_final_task = data[
                "instructionsAfterFinalTask"
            ]

            practice_task_data = data["practiceTask"]
            if experiment.practice_task is not None and (
                practice_task_data is None
                or "id" not in practice_task_data
                or experiment.practice_task.id != uuid.UUID(practice_task_data["id"])
            ):
                experiment.practice_task.delete()
                experiment.practice_task = None
            if practice_task_data is not None:
                experiment.practice_task = self._get_task(practice_task_data.get("id"))
                experiment.practice_task.label = practice_task_data["label"]
                experiment.practice_task.data = practice_task_data["data"]
                experiment.practice_task.save()

            experiment.save()

            tasks_to_delete = set(experiment.tasks.all())
            for task_data in data["tasks"]:
                task = self._get_task(task_data.get("id"))
                if task in tasks_to_delete:
                    tasks_to_delete.remove(task)
                task.experiment = experiment
                task.label = task_data["label"]
                task.data = task_data["data"]
                task.save()
            for task in tasks_to_delete:
                task.delete()

            experiment.required_experiments.set(data.get("requirements", []))

            for participant_id, assignments in data["assignments"].items():
                try:
                    participant_id = uuid.UUID(participant_id)
                    participant = models.Participant.objects.get(id=participant_id)
                except (models.Participant.DoesNotExist, ValueError):
                    participant = models.Participant.objects.get(label=participant_id)
                experiment.get_assignments(participant).filter(
                    started_time__isnull=True
                ).delete()
                for assignment in assignments:
                    if "id" in assignment:
                        task = experiment.tasks.get(id=assignment["id"])
                    elif "label" in assignment:
                        task = experiment.tasks.get(label=assignment["label"])
                    else:
                        return JsonResponse(
                            {"message": "Missing task ID or label"},
                            status=400,
                        )
                    if assignment.get("started", False):
                        continue
                    models.TaskAssignment.objects.create(
                        participant=participant,
                        task=task,
                    )

            experiment.ratings.all().delete()
            for rating_data in data["ratings"]:
                rating = self._get_rating(rating_data.get("id"))
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
        except KeyError as e:
            return JsonResponse(
                {"message": f"Missing key: {e}"},
                status=400,
            )

    @staticmethod
    def _get_experiment(experiment_id) -> models.Experiment:
        if experiment_id is not None:
            try:
                return models.Experiment.objects.get(id=experiment_id)
            except models.Experiment.DoesNotExist:
                return models.Experiment(id=experiment_id)
        else:
            return models.Experiment()

    @staticmethod
    def _get_task(task_id) -> models.Task:
        if task_id is not None:
            try:
                return models.Task.objects.get(id=task_id)
            except models.Task.DoesNotExist:
                return models.Task(id=task_id)
        else:
            return models.Task()

    @staticmethod
    def _get_rating(rating_id) -> models.TaskRating:
        if rating_id is not None:
            try:
                return models.TaskRating.objects.get(id=rating_id)
            except models.TaskRating.DoesNotExist:
                return models.TaskRating(id=rating_id)
        else:
            return models.TaskRating()


def experiment_results(request, experiment_id):
    download = "download" in request.GET
    experiment = models.Experiment.objects.get(id=experiment_id)
    data = {
        "experiment": {
            "id": experiment.id,
            "title": experiment.title,
            "task_type": experiment.task_type,
        },
        "results": [
            {
                "participant": participant.id,
                "practiceTasks": [
                    {
                        "id": assignment.task.id,
                        "label": assignment.task.label,
                        "results": assignment.results,
                        "started_time": assignment.started_time,
                        "finished_time": assignment.finished_time,
                    }
                    for assignment in experiment.get_assignments(
                        participant, practice=True
                    ).filter(results__isnull=False)
                ],
                "tasks": [
                    {
                        "id": assignment.task.id,
                        "label": assignment.task.label,
                        "results": assignment.results,
                        "started_time": assignment.started_time,
                        "finished_time": assignment.finished_time,
                    }
                    for assignment in experiment.get_assignments(participant).filter(
                        results__isnull=False
                    )
                ],
            }
            for participant in models.Participant.objects.all()
        ],
    }
    response = JsonResponse(
        data,
        status=200,
    )
    if download:
        response["Content-Disposition"] = f"attachment; filename={experiment.id}.json"
    return response


def experiment_results_graph(request, experiment_id, participant_id):
    experiment = models.Experiment.objects.get(id=experiment_id)
    participant = models.Participant.objects.get(id=participant_id)

    def random_color():
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    tasks = []
    label_colors = {}
    assignments = itertools.chain(
        experiment.get_assignments(participant, practice=True),
        experiment.get_assignments(participant),
    )
    for assignment in assignments:
        if assignment.results is not None:
            results = assignment.results
            start_timestamp = datetime.fromisoformat(
                results["events"][0]["time"].replace("Z", "+00:00")
            ).timestamp()
            for event in results["events"]:
                time = datetime.fromisoformat(event["time"].replace("Z", "+00:00"))
                event["time"] = (time.timestamp() - start_timestamp) * 100
                event["color"] = label_colors.setdefault(event["label"], random_color())
            tasks.append(
                {
                    "task": str(assignment.task.id)
                    + (
                        " (practice)"
                        if assignment.task == experiment.practice_task
                        else ""
                    ),
                    "results": assignment.results,
                    "started_time": assignment.started_time,
                    "finished_time": assignment.finished_time,
                    "graph_width": results["events"][-1]["time"] + 20,
                }
            )
    return render(
        request,
        "okra_server/experiment_results_graph.html",
        {
            "experiment": experiment,
            "participant": participant.id,
            "tasks": tasks,
        },
    )


@require_POST
def experiment_visibility(request, experiment_id):
    data = json.loads(request.body)
    visible = data["visible"]
    experiment = models.Experiment.objects.get(id=experiment_id)
    experiment.visible = visible
    experiment.save()
    return HttpResponse(status=200)


@require_POST
def delete_experiment(request, experiment_id):
    experiment = models.Experiment.objects.get(id=experiment_id)
    experiment.delete()
    return redirect("experiment-list")


class ParticipantList(ListView):
    model = models.Participant


@require_POST
def new_participant(request):
    models.Participant.objects.create()
    return redirect("participant-list")


@require_POST
def label_participant(request, participant_id):
    new_label = request.POST["label"]
    participant = models.Participant.objects.get(id=participant_id)
    participant.label = new_label
    participant.save()
    return redirect("participant-list")


@require_POST
def unregister_participant(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    participant.unregister()
    participant.save()
    return redirect("participant-list")


@require_POST
def delete_participant(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    participant.delete()
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

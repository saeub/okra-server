import base64
import io
import json

import qrcode
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, View

from okra_server import models


def registration_detail(request: HttpRequest, participant_id: str):
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
                    "title": experiment.title,
                    "instructions": experiment.instructions,
                    "practiceTask": {
                        "id": str(experiment.practice_task.id),
                        "label": experiment.practice_task.label,
                        "data": experiment.practice_task.data,
                    }
                    if experiment.practice_task is not None
                    else None,
                    "tasks": [
                        {
                            "id": str(task.id),
                            "label": task.label,
                            "data": task.data,
                        }
                        for task in experiment.tasks.all()
                    ],
                    "assignments": [
                        {
                            "participant": str(participant.id),
                            "tasks": [
                                str(assignment.task.id)
                                for assignment in experiment.get_assignments(
                                    participant
                                )
                            ],
                        }
                        for participant in models.Participant.objects.all()
                    ],
                },
            },
        )

    def post(self, request, experiment_id=None):
        experiment = self._get_experiment(experiment_id)
        data = json.loads(request.body)

        experiment.title = data["title"]
        experiment.instructions = data["instructions"]

        if experiment.practice_task is not None:
            experiment.practice_task.delete()
            experiment.practice_task = None
        practice_task_data = data["practiceTask"]
        if practice_task_data is not None:
            experiment.practice_task = self._get_task(practice_task_data["id"])
            experiment.practice_task.label = practice_task_data["label"]
            experiment.practice_task.data = practice_task_data["data"]
            experiment.practice_task.save()

        experiment.save()

        experiment.tasks.all().delete()
        for task_data in data["tasks"]:
            task = self._get_task(task_data["id"])
            task.experiment = experiment
            task.label = task_data["label"]
            task.data = task_data["data"]
            task.save()
        for assignment_data in data["assignments"]:
            for task_id in assignment_data["tasks"]:
                models.TaskAssignment.objects.create(
                    participant_id=assignment_data["participant"],
                    task_id=task_id,
                )

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


class ParticipantList(ListView):
    model = models.Participant


@require_POST
def new_participant(request):
    models.Participant.objects.create()
    return redirect("participant-list")

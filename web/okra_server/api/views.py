import json
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from okra_server import exceptions, models

MISSING_HEADERS_RESPONSE = JsonResponse(
    {
        "error": "Missing headers",
    },
    status=400,
)
INVALID_CREDENTIALS_RESPONSE = JsonResponse(
    {
        "error": "Invalid credentials",
    },
    status=401,
)
NOT_FOUND_RESPONSE = JsonResponse(
    {
        "error": "Not found",
    },
    status=404,
)
NO_ASSIGNABLE_TASKS_RESPONSE = JsonResponse(
    {
        "error": "No tasks left",
    },
    status=404,
)


def api_view(method: str, check_credentials: bool = False, query_params: bool = False):
    def decorator(view):
        @wraps(view)
        @require_http_methods([method])
        @csrf_exempt
        def inner(request: HttpRequest, *args, **kwargs):
            participant = None
            if check_credentials:
                participant_id = request.headers.get("X-Participant-ID")
                device_key = request.headers.get("X-Device-Key")
                if not participant_id or not device_key:
                    return MISSING_HEADERS_RESPONSE

                try:
                    participant = models.Participant.objects.get(
                        id=participant_id, device_key=device_key
                    )
                except (models.Participant.DoesNotExist, ValidationError):
                    return INVALID_CREDENTIALS_RESPONSE

            if request.method == "GET":
                data = request.GET

            elif request.method == "POST" and request.body:
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return HttpResponseBadRequest()

            else:
                data = {}

            if query_params:
                kwargs["query_params"] = request.GET

            return view(data, *args, participant=participant, **kwargs)

        return inner

    return decorator


def _serialize_experiment(
    experiment: models.Experiment, participant: models.Participant
) -> dict:
    return {
        "id": experiment.id,
        "type": experiment.task_type,
        "title": experiment.title,
        "coverImageUrl": experiment.cover_image_url,
        "instructions": experiment.instructions,
        "nTasks": experiment.get_n_tasks(participant),
        "nTasksDone": experiment.get_n_tasks(participant, started=True),
        "hasPracticeTask": experiment.practice_task is not None,
        "ratings": [_serialize_rating(rating) for rating in experiment.ratings.all()],
    }


def _serialize_task(task: models.Task, *, is_final: bool) -> dict:
    if task.is_practice:
        instructions_after = (
            task.practice_experiment.instructions_after_practice_task
            or task.practice_experiment.instructions_after_task
        )
    elif is_final:
        instructions_after = (
            task.experiment.instructions_after_final_task
            or task.experiment.instructions_after_task
        )
    else:
        instructions_after = task.experiment.instructions_after_task

    return {
        "id": task.id,
        "data": task.data,
        "instructionsAfter": instructions_after or None,
    }


def _serialize_rating(rating: models.TaskRating) -> dict:
    return {
        "question": rating.question,
        "type": rating.rating_type,
        "lowExtreme": rating.low_extreme,
        "highExtreme": rating.high_extreme,
    }


@api_view("GET")
def base(data: dict, **kwargs):
    return JsonResponse(
        {
            "name": settings.API_INFO["name"],
            "iconUrl": settings.API_INFO["icon_url"],
        }
    )


@api_view("POST")
def register(data: dict, **kwargs):
    participant_id = data.get("participantId")
    registration_key = data.get("registrationKey")
    if not participant_id or not registration_key:
        return HttpResponseBadRequest()
    try:
        participant = models.Participant.objects.get(
            id=participant_id,
            registration_key=registration_key,
        )
    except (models.Participant.DoesNotExist, ValidationError):
        return INVALID_CREDENTIALS_RESPONSE
    participant.register()
    participant.save()
    return JsonResponse(
        {
            "name": settings.API_INFO["name"],
            "iconUrl": settings.API_INFO["icon_url"],
            "participantId": participant.id,
            "deviceKey": participant.device_key,
        }
    )


@api_view("GET", check_credentials=True)
def get_experiments(data: dict, participant: models.Participant):
    return JsonResponse(
        {
            "experiments": [
                _serialize_experiment(experiment, participant)
                for experiment in participant.experiments
                if experiment.is_available(participant)
            ],
        }
    )


@api_view("GET", check_credentials=True)
def get_experiment(data: dict, experiment_id: str, participant: models.Participant):
    try:
        experiment = participant.experiments.get(id=experiment_id)
        if not experiment.is_available(participant):
            return NOT_FOUND_RESPONSE
    except models.Experiment.DoesNotExist:
        return NOT_FOUND_RESPONSE
    return JsonResponse(_serialize_experiment(experiment, participant))


@api_view("POST", check_credentials=True, query_params=True)
def start_task(
    data: dict, experiment_id: str, participant: models.Participant, query_params: dict
):
    try:
        experiment = participant.experiments.get(id=experiment_id)
        if not experiment.is_available(participant):
            return NOT_FOUND_RESPONSE
    except models.Experiment.DoesNotExist:
        return NOT_FOUND_RESPONSE
    try:
        task = experiment.start_task(
            participant, query_params.get("practice") == "true"
        )
    except exceptions.NoTasksAvailable:
        return NO_ASSIGNABLE_TASKS_RESPONSE
    n_tasks = experiment.get_n_tasks(participant)
    n_tasks_done = experiment.get_n_tasks(participant, started=True)
    return JsonResponse(_serialize_task(task, is_final=n_tasks_done == n_tasks))


@api_view("POST", check_credentials=True)
def finish_task(data: dict, task_id: str, participant: models.Participant):
    try:
        task = models.Task.objects.get(id=task_id)
        task.finish(participant, data)
    except (models.Task.DoesNotExist, models.TaskAssignment.DoesNotExist):
        return NOT_FOUND_RESPONSE
    return JsonResponse({})

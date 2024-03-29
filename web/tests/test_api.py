import pytest

from okra_server.models import Experiment, Task, TaskAssignment, TaskType


@pytest.fixture
def experiment(registered_participant):
    pt = Task.objects.create(
        data={"practice": "task"},
    )
    e = Experiment.objects.create(
        task_type=TaskType.QUESTION_ANSWERING,
        title="Test experiment",
        instructions="Read the text and answer the questions.",
        instructions_after_task="You've completed the task.",
        instructions_after_practice_task="You've completed the practice task.",
        practice_task=pt,
        visible=True,
    )
    t = Task.objects.create(
        experiment=e,
        data={
            "segments": [
                {
                    "text": "This is an .",
                    "blankPosition": 11,
                    "options": ["example", "text", "pineapple"],
                    "correctOptionIndex": 0,
                },
            ],
        },
    )
    TaskAssignment.objects.create(
        participant=registered_participant,
        task=t,
    )
    return e


def test_register(client, unregistered_participant):
    response = client.post(
        "/api/register",
        {
            "participantId": unregistered_participant.id,
            "registrationKey": unregistered_participant.registration_key,
        },
        content_type="application/json",
    )
    unregistered_participant.refresh_from_db()
    assert response.status_code == 200, response.content
    assert response.json()["participantId"] == str(unregistered_participant.id)
    assert response.json()["deviceKey"] == unregistered_participant.device_key
    assert unregistered_participant.registration_key is None


def test_experiments(client, registered_participant, experiment):
    response = client.get(
        "/api/experiments",
        HTTP_X_PARTICIPANT_ID="incorrect_id",
        HTTP_X_DEVICE_KEY="incorrect_key",
    )
    assert response.status_code == 401, response.content

    response = client.get(
        "/api/experiments",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert len(response.json()["experiments"]) == 1
    assert response.json()["experiments"][0]["id"] == str(experiment.id)
    assert response.json()["experiments"][0]["nTasks"] == 1
    assert response.json()["experiments"][0]["nTasksDone"] == 0
    assert response.json()["experiments"][0]["hasPracticeTask"] is True


def test_start_finish_task(client, registered_participant, experiment):
    assignment = registered_participant.assignments.get()
    assert assignment.started_time is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    response = client.post(
        f"/api/experiments/{experiment.id}/start",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 200, response.content
    assert response.json()["id"] == str(assignment.task.id)
    assert response.json()["data"] == assignment.task.data
    assert response.json()["instructionsAfter"] == experiment.instructions_after_task
    assert assignment.started_time is not None
    assert assignment.finished_time is None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 1

    results = {
        "data": {"dummy_key": "dummy_value"},
        "events": [{"time": "dummy_time", "label": "dummy_label", "data": None}],
    }
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 200, response.content
    assert assignment.started_time is not None
    assert assignment.finished_time is not None
    assert assignment.results == results
    assert experiment.get_n_tasks(registered_participant, started=True) == 1


def test_start_restart_task(client, registered_participant, experiment):
    assignment = registered_participant.assignments.get()
    assert assignment.started_time is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    response = client.post(
        f"/api/experiments/{experiment.id}/start",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 200, response.content
    assert response.json()["id"] == str(assignment.task.id)
    assert response.json()["data"] == assignment.task.data
    assert response.json()["instructionsAfter"] == experiment.instructions_after_task
    assert assignment.started_time is not None
    assert assignment.finished_time is None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 1

    # Start next task without finishing
    response = client.post(
        f"/api/experiments/{experiment.id}/start",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 404, response.content
    assert response.json()["error"] == "No tasks left"
    assert assignment.started_time is not None
    assert assignment.finished_time is not None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 1


def test_start_finish_practice_task(client, registered_participant, experiment):
    with pytest.raises(TaskAssignment.DoesNotExist):
        registered_participant.assignments.get(
            task=experiment.practice_task, finished_time=None
        )
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    response = client.post(
        f"/api/experiments/{experiment.id}/start?practice=true",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment = registered_participant.assignments.get(
        task=experiment.practice_task, finished_time=None
    )
    assert response.status_code == 200, response.content
    assert (
        response.json()["id"]
        == str(assignment.task.id)
        == str(experiment.practice_task.id)
    )
    assert (
        response.json()["data"] == assignment.task.data == experiment.practice_task.data
    )
    assert assignment.started_time is not None
    assert assignment.finished_time is None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    results = {
        "data": {"dummy_key": "dummy_value"},
        "events": [{"time": "dummy_time", "label": "dummy_label", "data": None}],
    }
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 200, response.content
    assert assignment.started_time is not None
    assert assignment.finished_time is not None
    assert assignment.results == results
    assert experiment.get_n_tasks(registered_participant, started=True) == 0


def test_start_restart_finish_practice_task(client, registered_participant, experiment):
    with pytest.raises(TaskAssignment.DoesNotExist):
        registered_participant.assignments.get(
            task=experiment.practice_task, finished_time=None
        )
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    response = client.post(
        f"/api/experiments/{experiment.id}/start?practice=true",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment = registered_participant.assignments.get(
        task=experiment.practice_task, finished_time=None
    )
    assert response.status_code == 200, response.content
    assert (
        response.json()["id"]
        == str(assignment.task.id)
        == str(experiment.practice_task.id)
    )
    assert (
        response.json()["data"] == assignment.task.data == experiment.practice_task.data
    )
    assert (
        response.json()["instructionsAfter"]
        == assignment.task.practice_experiment.instructions_after_practice_task
        == experiment.instructions_after_practice_task
    )
    assert assignment.started_time is not None
    assert assignment.finished_time is None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    # Restart practice task without finishing
    response = client.post(
        f"/api/experiments/{experiment.id}/start?practice=true",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert assignment.started_time is not None
    assert assignment.finished_time is not None
    assert assignment.results is None
    assignment = registered_participant.assignments.get(
        task=experiment.practice_task, finished_time=None
    )
    assert response.status_code == 200, response.content
    assert (
        response.json()["id"]
        == str(assignment.task.id)
        == str(experiment.practice_task.id)
    )
    assert (
        response.json()["data"] == assignment.task.data == experiment.practice_task.data
    )
    assert (
        response.json()["instructionsAfter"]
        == assignment.task.practice_experiment.instructions_after_practice_task
        == experiment.instructions_after_practice_task
    )
    assert assignment.started_time is not None
    assert assignment.finished_time is None
    assert assignment.results is None
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    results = {
        "data": {"dummy_key": "dummy_value"},
        "events": [{"time": "dummy_time", "label": "dummy_label", "data": None}],
    }
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assignment.refresh_from_db()
    assert response.status_code == 200, response.content
    assert assignment.started_time is not None
    assert assignment.finished_time is not None
    assert assignment.results == results
    assert experiment.get_n_tasks(registered_participant, started=True) == 0


def test_instructions(client, registered_participant, experiment):
    experiment.instructions_after_final_task = "You've completed the final task."
    experiment.save()
    final_task = Task.objects.create(
        experiment=experiment,
        data={
            "segments": [
                {
                    "text": "This is another .",
                    "blankPosition": 16,
                    "options": ["example", "text", "pineapple"],
                    "correctOptionIndex": 0,
                },
            ],
        },
    )
    TaskAssignment.objects.create(
        participant=registered_participant,
        task=final_task,
    )
    results = {
        "data": {"dummy_key": "dummy_value"},
        "events": [{"time": "dummy_time", "label": "dummy_label", "data": None}],
    }

    # Practice task
    response = client.post(
        f"/api/experiments/{experiment.id}/start?practice=true",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert response.json()["instructionsAfter"] == "You've completed the practice task."
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert experiment.get_n_tasks(registered_participant, started=True) == 0

    # First task
    response = client.post(
        f"/api/experiments/{experiment.id}/start",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert response.json()["instructionsAfter"] == "You've completed the task."
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert experiment.get_n_tasks(registered_participant, started=True) == 1

    # Final task
    response = client.post(
        f"/api/experiments/{experiment.id}/start",
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert response.json()["instructionsAfter"] == "You've completed the final task."
    response = client.post(
        f"/api/tasks/{response.json()['id']}/finish",
        results,
        content_type="application/json",
        HTTP_X_PARTICIPANT_ID=registered_participant.id,
        HTTP_X_DEVICE_KEY=registered_participant.device_key,
    )
    assert response.status_code == 200, response.content
    assert experiment.get_n_tasks(registered_participant, started=True) == 2

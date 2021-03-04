import pytest
from django.template.defaultfilters import escapejs

from okra_server.models import Experiment, Participant, Task, TaskAssignment, TaskType


@pytest.fixture
def experiments(registered_participant):
    e1 = Experiment.objects.create(
        task_type=TaskType.QUESTION_ANSWERING,
        title="Test experiment",
        instructions="Read the text and answer the questions.",
    )
    t1 = Task.objects.create(
        experiment=e1,
        data={},
    )
    TaskAssignment.objects.create(
        participant=registered_participant,
        task=t1,
    )
    e2 = Experiment.objects.create(
        task_type=TaskType.QUESTION_ANSWERING,
        title="Test experiment",
        instructions="Read the text and answer the questions.",
    )
    t1 = Task.objects.create(
        experiment=e1,
        data={},
    )
    return [e1, e2]


@pytest.fixture
def public_urls(unregistered_participant):
    return [
        f"/registration/{unregistered_participant.id}",
    ]


@pytest.fixture
def private_urls(experiments):
    return [
        "/experiments",
        "/experiments/new",
        f"/experiments/{experiments[0].id}",
        "/participants",
    ]


def test_get_registration_detail(authenticated_client, unregistered_participant):
    response = authenticated_client.get(f"/registration/{unregistered_participant.id}")
    assert response.status_code == 200, response.content
    assert str(unregistered_participant.id) in response.content.decode()
    assert unregistered_participant.registration_key in response.content.decode()


def test_get_registration_detail_already_registered(
    authenticated_client, registered_participant
):
    response = authenticated_client.get(f"/registration/{registered_participant.id}")
    assert response.status_code == 404, response.content
    assert "already registered" in response.content.decode()


def test_unauthenticated(client, public_urls, private_urls):
    for url in public_urls:
        response = client.get(url)
        assert client.get(url).status_code == 200, response.content
    for url in private_urls:
        response = client.get(url)
        assert response.status_code == 302, response.content
        assert response.url == f"/login?next={url}"


def test_authenticated(authenticated_client, public_urls, private_urls):
    for url in public_urls:
        response = authenticated_client.get(url)
        assert response.status_code == 200, response.content
    for url in private_urls:
        response = authenticated_client.get(url)
        assert response.status_code == 200, response.content


def test_get_experiment_list(authenticated_client, experiments):
    response = authenticated_client.get("/experiments")
    assert response.status_code == 200, response.content
    for experiment in experiments:
        assert str(experiment.id) in response.content.decode()


def test_get_experiment_detail(authenticated_client, experiments):
    for experiment in experiments:
        response = authenticated_client.get(f"/experiments/{experiment.id}")
        assert response.status_code == 200, response.content
        for task in experiment.tasks.all():
            assert escapejs(str(task.id)) in response.content.decode()


def test_post_experiment_detail(authenticated_client, experiments):
    for experiment in experiments:
        data = {
            "title": "New title",
            "instructions": "New instructions",
            "tasks": [
                {
                    "id": str(task.id),
                    "label": "New label",
                    "data": {"new": "data"},
                }
                for task in experiment.tasks.all()
            ],
            "assignments": [
                {
                    "participant": str(participant.id),
                    "tasks": [str(task.id) for task in experiment.tasks.all()],
                }
                for participant in Participant.objects.all()
            ],
        }
        response = authenticated_client.post(
            f"/experiments/{experiment.id}", data, content_type="application/json"
        )
        assert response.status_code == 200, response.content
        experiment.refresh_from_db()
        assert experiment.title == "New title"
        assert experiment.instructions == "New instructions"
        for task in experiment.tasks.all():
            assert task.label == "New label"
            assert task.data == {"new": "data"}
        for participant in Participant.objects.all():
            assert (
                experiment.get_assignments(participant).count()
                == experiment.tasks.count()
            )


def test_post_experiment_detail_delete_tasks(authenticated_client, experiments):
    for experiment in experiments:
        data = {
            "title": "New title",
            "instructions": "New instructions",
            "tasks": [],
            "assignments": [],
        }
        response = authenticated_client.post(
            f"/experiments/{experiment.id}", data, content_type="application/json"
        )
        assert response.status_code == 200, response.content
        experiment.refresh_from_db()
        assert experiment.tasks.count() == 0
        for participant in Participant.objects.all():
            assert experiment.get_assignments(participant).count() == 0


def test_get_participant_list(
    authenticated_client, unregistered_participant, registered_participant
):
    response = authenticated_client.get("/participants")
    assert response.status_code == 200, response.content
    assert str(unregistered_participant.id) in response.content.decode()
    assert str(registered_participant.id) in response.content.decode()

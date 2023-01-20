from uuid import uuid4

import pytest
from django.template.defaultfilters import escapejs

from okra_server import models


@pytest.fixture
def experiments(registered_participant):
    pt = models.Task.objects.create(
        data={"practice": "task"},
    )
    e1 = models.Experiment.objects.create(
        task_type=models.TaskType.QUESTION_ANSWERING,
        title="Test experiment",
        instructions="Read the text and answer the questions.",
        practice_task=pt,
    )
    t1 = models.Task.objects.create(
        experiment=e1,
        data={},
    )
    models.TaskAssignment.objects.create(
        participant=registered_participant,
        task=t1,
    )
    e2 = models.Experiment.objects.create(
        task_type=models.TaskType.QUESTION_ANSWERING,
        title="Test experiment",
        instructions="Read the text and answer the questions.",
        instructions_after_task="You've completed the task.",
    )
    t2 = models.Task.objects.create(
        experiment=e2,
        data={},
    )
    models.TaskAssignment.objects.create(
        participant=registered_participant,
        task=t2,
    )
    models.TaskRating.objects.create(
        experiment=e2,
        question="Rating",
        rating_type="slider",
    )
    return [e1, e2]


@pytest.fixture
def public_urls(unregistered_participant):
    return [
        "/",
        "/login",
        f"/registration/{unregistered_participant.id}",
    ]


@pytest.fixture
def private_urls(experiments):
    return [
        "/participants",
        "/experiments",
        f"/progress/{experiments[0].id}",
    ]


@pytest.fixture
def staff_urls(experiments, registered_participant):
    return [
        "/experiments/new",
        f"/experiments/{experiments[0].id}",
        f"/experiments/{experiments[0].id}/results",
        f"/experiments/{experiments[0].id}/results?download",
        f"/experiments/{experiments[0].id}/results/{registered_participant.id}/graph",
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


def test_unauthenticated(client, public_urls, private_urls, staff_urls):
    for url in public_urls:
        response = client.get(url)
        assert response.status_code == 200, url
    for url in private_urls:
        response = client.get(url)
        assert response.status_code == 302, url
        assert response.url == f"/login?next={url.replace('?', '%3F')}"
    for url in staff_urls:
        response = client.get(url)
        assert response.status_code == 302, url
        assert response.url == f"/login?next={url.replace('?', '%3F')}"


def test_authenticated(authenticated_client, public_urls, private_urls, staff_urls):
    for url in public_urls:
        response = authenticated_client.get(url)
        assert response.status_code == 200, url
    for url in private_urls:
        response = authenticated_client.get(url)
        assert response.status_code == 200, url
    for url in staff_urls:
        response = authenticated_client.get(url)
        assert response.status_code == 302, url
        assert response.url == f"/login?next={url.replace('?', '%3F')}"


def test_authenticated_staff(
    staff_authenticated_client, public_urls, private_urls, staff_urls
):
    for url in public_urls:
        response = staff_authenticated_client.get(url)
        assert response.status_code == 200, url
    for url in private_urls:
        response = staff_authenticated_client.get(url)
        assert response.status_code == 200, url
    for url in staff_urls:
        response = staff_authenticated_client.get(url)
        assert response.status_code == 200, url


def test_get_index(client, experiments, registered_participant):
    response = client.get("/")
    assert response.status_code == 200, response.content
    for experiment in experiments:
        assert str(experiment.id) not in response.content.decode()
    assert response.content.decode().count(str(registered_participant.id)) == 0


def test_get_index_authenticated(staff_authenticated_client, experiments):
    response = staff_authenticated_client.get("/")
    assert response.status_code == 200, response.content
    for experiment in experiments:
        assert str(experiment.id) in response.content.decode()


def test_get_progress_authenticated(
    staff_authenticated_client, experiments, registered_participant
):
    response = staff_authenticated_client.get(f"/progress/{experiments[0].id}")
    assert response.status_code == 200, response.content
    assert str(experiments[0].id) in response.content.decode()
    assert (
        response.content.decode().count(str(registered_participant.id)) == 2
    )  # Two occurrences: once as a heading, once as a button


def test_get_experiment_list(staff_authenticated_client, experiments):
    response = staff_authenticated_client.get("/experiments")
    assert response.status_code == 200, response.content
    for experiment in experiments:
        assert str(experiment.id) in response.content.decode()
    assert response.content.decode().count('data-bs-target="#delete-modal"') == len(
        experiments
    )


def test_get_experiment_detail(staff_authenticated_client, experiments):
    for experiment in experiments:
        response = staff_authenticated_client.get(f"/experiments/{experiment.id}")
        assert response.status_code == 200, response.content
        for task in experiment.tasks.all():
            assert escapejs(str(task.id)) in response.content.decode()
        for rating in experiment.ratings.all():
            assert escapejs(str(rating.id)) in response.content.decode()


def test_post_experiment_detail(staff_authenticated_client, experiments):
    for experiment in experiments:
        data = {
            "taskType": "cloze",
            "title": "New title",
            "instructions": "New instructions",
            "instructionsAfterTask": "You've completed the task.",
            "instructionsAfterPracticeTask": "You've completed the practice task.",
            "instructionsAfterFinalTask": "You've completed the final task.",
            "practiceTask": {
                "id": str(experiment.practice_task.id),
                "label": "New practice task",
                "data": {"new": "practice data"},
            }
            if experiment.practice_task is not None
            else None,
            "tasks": [
                {
                    "id": str(task.id),
                    "label": "New label",
                    "data": {"new": "data"},
                }
                for task in experiment.tasks.all()
            ],
            "ratings": [
                {
                    "id": str(rating.id),
                    "question": "New rating",
                    "type": "emoticon",
                    "lowExtreme": "New low extreme",
                    "highExtreme": "New high extreme",
                }
                for rating in experiment.ratings.all()
            ],
            "assignments": {
                str(participant.id): [
                    {"id": str(task.id), "started": False}
                    for task in experiment.tasks.all()
                ]
                for participant in models.Participant.objects.all()
            },
        }
        task_count_before = experiment.tasks.count()
        rating_count_before = experiment.ratings.count()
        response = staff_authenticated_client.post(
            f"/experiments/{experiment.id}", data, content_type="application/json"
        )
        assert response.status_code == 200, response.content
        experiment.refresh_from_db()
        assert experiment.task_type == "cloze"
        assert experiment.title == "New title"
        assert experiment.instructions == "New instructions"
        assert (
            experiment.instructions_after_practice_task
            == "You've completed the practice task."
        )
        assert experiment.instructions_after_task == "You've completed the task."
        assert (
            experiment.instructions_after_final_task
            == "You've completed the final task."
        )
        if experiment.practice_task is not None:
            assert experiment.practice_task.label == "New practice task"
            assert experiment.practice_task.data == {"new": "practice data"}
        assert experiment.tasks.count() == task_count_before
        for task in experiment.tasks.all():
            assert task.label == "New label"
            assert task.data == {"new": "data"}
        assert experiment.ratings.count() == rating_count_before
        for rating in experiment.ratings.all():
            assert rating.question == "New rating"
            assert rating.rating_type == "emoticon"
            assert rating.low_extreme == "New low extreme"
            assert rating.high_extreme == "New high extreme"
        for participant in models.Participant.objects.all():
            assert (
                experiment.get_assignments(participant).count()
                == experiment.tasks.count()
            )


def test_post_experiment_detail_clear(staff_authenticated_client, experiments):
    for experiment in experiments:
        data = {
            "taskType": "reading",
            "title": "",
            "instructions": "",
            "instructionsAfterTask": None,
            "instructionsAfterPracticeTask": None,
            "instructionsAfterFinalTask": None,
            "practiceTask": None,
            "tasks": [],
            "ratings": [],
            "assignments": {},
        }
        response = staff_authenticated_client.post(
            f"/experiments/{experiment.id}", data, content_type="application/json"
        )
        assert response.status_code == 200, response.content
        experiment.refresh_from_db()
        assert experiment.task_type == "reading"
        assert experiment.title == ""
        assert experiment.instructions == ""
        assert experiment.instructions_after_practice_task is None
        assert experiment.instructions_after_task is None
        assert experiment.instructions_after_final_task is None
        assert experiment.practice_task is None
        assert experiment.tasks.count() == 0
        assert experiment.ratings.count() == 0
        for participant in models.Participant.objects.all():
            assert experiment.get_assignments(participant).count() == 0


def test_post_experiment_detail_new_with_ids(
    staff_authenticated_client, unregistered_participant, registered_participant
):
    experiment_id = uuid4()
    practice_task_id = uuid4()
    task_id = uuid4()
    rating_id = uuid4()
    data = {
        "id": experiment_id,
        "taskType": "reading",
        "title": "test title",
        "instructions": "test instructions",
        "instructionsAfterTask": "test instructions after task",
        "instructionsAfterPracticeTask": "test instructions after practice task",
        "instructionsAfterFinalTask": "test instructions after final task",
        "practiceTask": {
            "id": practice_task_id,
            "label": "test practice task",
            "data": {"test": "practice data"},
        },
        "tasks": [
            {
                "id": task_id,
                "label": "test task",
                "data": {"test": "data"},
            },
        ],
        "ratings": [
            {
                "id": rating_id,
                "question": "test rating",
                "type": "emoticon",
                "lowExtreme": "test low extreme",
                "highExtreme": "test high extreme",
            },
        ],
        "assignments": {
            str(unregistered_participant.id): [
                {"id": task_id},
            ],
            str(registered_participant.id): [
                {"id": task_id},
            ],
        },
    }
    response = staff_authenticated_client.post(
        "/experiments/new", data, content_type="application/json"
    )
    assert response.status_code == 200, response.content

    experiment = models.Experiment.objects.get(id=experiment_id)
    assert experiment.task_type == "reading"
    assert experiment.title == "test title"
    assert experiment.instructions == "test instructions"
    assert (
        experiment.instructions_after_practice_task
        == "test instructions after practice task"
    )
    assert experiment.instructions_after_task == "test instructions after task"
    assert (
        experiment.instructions_after_final_task == "test instructions after final task"
    )

    practice_task = experiment.practice_task
    assert practice_task.id == practice_task_id
    assert practice_task.label == "test practice task"
    assert practice_task.data == {"test": "practice data"}

    task = experiment.tasks.get(id=task_id)
    assert task.label == "test task"
    assert task.data == {"test": "data"}

    rating = experiment.ratings.get(id=rating_id)
    assert rating.question == "test rating"
    assert rating.rating_type == "emoticon"
    assert rating.low_extreme == "test low extreme"
    assert rating.high_extreme == "test high extreme"

    assert (
        experiment.get_assignments(unregistered_participant).get(task=task).started_time
        is None
    )
    assert (
        experiment.get_assignments(registered_participant).get(task=task).started_time
        is None
    )


def test_post_experiment_detail_new_without_ids(
    staff_authenticated_client, unregistered_participant, registered_participant
):
    unregistered_participant.label = "test participant 1"
    unregistered_participant.save()
    registered_participant.label = "test participant 2"
    registered_participant.save()
    data = {
        "taskType": "reading",
        "title": "test title",
        "instructions": "test instructions",
        "instructionsAfterTask": "test instructions after task",
        "instructionsAfterPracticeTask": "test instructions after practice task",
        "instructionsAfterFinalTask": "test instructions after final task",
        "practiceTask": {
            "label": "test practice task",
            "data": {"test": "practice data"},
        },
        "tasks": [
            {
                "label": "test task",
                "data": {"test": "data"},
            },
        ],
        "ratings": [
            {
                "question": "test rating",
                "type": "emoticon",
                "lowExtreme": "test low extreme",
                "highExtreme": "test high extreme",
            },
        ],
        "assignments": {
            str(unregistered_participant.label): [
                {"label": "test task"},
            ],
            str(registered_participant.label): [
                {"label": "test task"},
            ],
        },
    }
    response = staff_authenticated_client.post(
        "/experiments/new", data, content_type="application/json"
    )
    assert response.status_code == 200, response.content

    experiment = models.Experiment.objects.get(title="test title")
    assert experiment.task_type == "reading"
    assert experiment.title == "test title"
    assert experiment.instructions == "test instructions"
    assert (
        experiment.instructions_after_practice_task
        == "test instructions after practice task"
    )
    assert experiment.instructions_after_task == "test instructions after task"
    assert (
        experiment.instructions_after_final_task == "test instructions after final task"
    )

    practice_task = experiment.practice_task
    assert practice_task.label == "test practice task"
    assert practice_task.data == {"test": "practice data"}

    task = experiment.tasks.get(label="test task")
    assert task.label == "test task"
    assert task.data == {"test": "data"}

    rating = experiment.ratings.get(question="test rating")
    assert rating.question == "test rating"
    assert rating.rating_type == "emoticon"
    assert rating.low_extreme == "test low extreme"
    assert rating.high_extreme == "test high extreme"


def test_post_experiment_detail_missing_key(staff_authenticated_client, experiments):
    for experiment in experiments:
        data = {
            "taskType": "reading",
            "title": "",
            "instructions": "",
            "instructionsAfterTask": None,
            "instructionsAfterPracticeTask": None,
            "instructionsAfterFinalTask": None,
            "practiceTask": None,
            "tasks": [],
            "ratings": [],
            "assignments": {},
        }
        response = staff_authenticated_client.post(
            f"/experiments/{experiment.id}", data, content_type="application/json"
        )
        for key in data:
            invalid_data = data.copy()
            del invalid_data[key]
            response = staff_authenticated_client.post(
                f"/experiments/{experiment.id}",
                invalid_data,
                content_type="application/json",
            )
            assert response.status_code == 400, response.content
            assert response.json() == {"message": f"Missing key: {key!r}"}


def test_post_delete_experiment(staff_authenticated_client, experiments):
    for experiment in experiments:
        staff_authenticated_client.post(f"/experiments/{experiment.id}/delete")
        with pytest.raises(models.Experiment.DoesNotExist):
            models.Experiment.objects.get(id=experiment.id)


def test_get_participant_list(
    authenticated_client, unregistered_participant, registered_participant
):
    response = authenticated_client.get("/participants")
    assert response.status_code == 200, response.content
    assert str(unregistered_participant.id) in response.content.decode()
    assert str(registered_participant.id) in response.content.decode()
    assert response.content.decode().count("Unregister") == 2
    assert response.content.decode().count("Delete") == 0


def test_get_participant_list_authenticated(
    staff_authenticated_client, unregistered_participant, registered_participant
):
    response = staff_authenticated_client.get("/participants")
    assert response.status_code == 200, response.content
    assert str(unregistered_participant.id) in response.content.decode()
    assert str(registered_participant.id) in response.content.decode()
    assert response.content.decode().count('data-bs-target="#unregister-modal"') == 1
    assert response.content.decode().count('data-bs-target="#delete-modal"') == 2


def test_post_label_participant(staff_authenticated_client, unregistered_participant):
    assert unregistered_participant.label == "unlabeled"
    staff_authenticated_client.post(
        f"/participants/{unregistered_participant.id}/label", {"label": "new label"}
    )
    unregistered_participant.refresh_from_db()
    assert unregistered_participant.label == "new label"


def test_post_unregister_participant(
    staff_authenticated_client, registered_participant
):
    assert registered_participant.device_key is not None
    staff_authenticated_client.post(
        f"/participants/{registered_participant.id}/unregister"
    )
    registered_participant.refresh_from_db()
    assert registered_participant.device_key is None


def test_post_delete_participant(
    staff_authenticated_client, unregistered_participant, registered_participant
):
    staff_authenticated_client.post(
        f"/participants/{unregistered_participant.id}/delete"
    )
    with pytest.raises(models.Participant.DoesNotExist):
        models.Participant.objects.get(id=unregistered_participant.id)

    staff_authenticated_client.post(f"/participants/{registered_participant.id}/delete")
    with pytest.raises(models.Participant.DoesNotExist):
        models.Participant.objects.get(id=registered_participant.id)

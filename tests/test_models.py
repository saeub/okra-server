import pytest

from okra_server.exceptions import NoTasksAvailable
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
        practice_task=pt,
    )
    t1 = Task.objects.create(
        experiment=e,
        data={},
    )
    TaskAssignment.objects.create(
        participant=registered_participant,
        task=t1,
    )
    t2 = Task.objects.create(
        experiment=e,
        data={},
    )
    TaskAssignment.objects.create(
        participant=registered_participant,
        task=t2,
    )
    return e


def test_participant_register(unregistered_participant):
    assert unregistered_participant.registration_key is not None
    assert unregistered_participant.device_key is None
    unregistered_participant.register()
    assert unregistered_participant.registration_key is None
    assert unregistered_participant.device_key is not None


def test_task_start_finish(registered_participant, experiment):
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks_done(registered_participant) == 0

    task1 = experiment.start_task(registered_participant)
    task1.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks_done(registered_participant) == 1

    task2 = experiment.start_task(registered_participant)
    assert task2 != task1
    task2.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks_done(registered_participant) == 2

    with pytest.raises(NoTasksAvailable):
        experiment.start_task(registered_participant)


def test_practice_task_start_finish(registered_participant, experiment):
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks_done(registered_participant) == 0

    practice_task = experiment.start_task(registered_participant, practice=True)
    assert practice_task.data == {"practice": "task"}
    practice_task.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks_done(registered_participant) == 0

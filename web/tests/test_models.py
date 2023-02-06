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
        visible=True,
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
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 0
    )

    task1 = experiment.start_task(registered_participant)
    assert experiment.get_n_tasks(registered_participant, started=True) == 1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    task1.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 1
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 0
    )

    task2 = experiment.start_task(registered_participant)
    assert task2 != task1
    assert experiment.get_n_tasks(registered_participant, started=True) == 2
    assert experiment.get_n_tasks(registered_participant, finished=True) == 1
    task2.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 2
    assert experiment.get_n_tasks(registered_participant, finished=True) == 2
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 0
    )

    with pytest.raises(NoTasksAvailable):
        experiment.start_task(registered_participant)


def test_practice_task_start_finish(registered_participant, experiment):
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert experiment.get_n_tasks(registered_participant, practice=True) == 0
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, finished=True)
        == 0
    )

    practice_task = experiment.start_task(registered_participant, practice=True)
    assert practice_task.data == {"practice": "task"}
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 1
    )
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, finished=True)
        == 0
    )
    practice_task.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 1
    )
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, finished=True)
        == 1
    )

    practice_task = experiment.start_task(registered_participant, practice=True)
    assert practice_task.data == {"practice": "task"}
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 2
    )
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, finished=True)
        == 1
    )
    practice_task.finish(registered_participant, {})

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, started=True) == 2
    )
    assert (
        experiment.get_n_tasks(registered_participant, practice=True, finished=True)
        == 2
    )


def test_task_start_cancel(registered_participant, experiment):
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 0

    task1 = experiment.start_task(registered_participant)
    assert experiment.get_n_tasks(registered_participant, started=True) == 1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 0
    task1.cancel(registered_participant)

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 1
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 1

    task2 = experiment.start_task(registered_participant)
    assert task2 != task1
    assert experiment.get_n_tasks(registered_participant, started=True) == 2
    assert experiment.get_n_tasks(registered_participant, finished=True) == 1
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 1
    task2.cancel(registered_participant)

    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 2
    assert experiment.get_n_tasks(registered_participant, finished=True) == 2
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 2

    with pytest.raises(NoTasksAvailable):
        experiment.start_task(registered_participant)


def test_task_start_start(registered_participant, experiment):
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 0
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 0

    task1 = experiment.start_task(registered_participant)
    assert experiment.get_n_tasks(registered_participant, started=True) == 1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 0
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 0

    task2 = experiment.start_task(registered_participant)
    assert task2 != task1
    assert experiment.get_n_tasks(registered_participant) == 2
    assert experiment.get_n_tasks(registered_participant, started=True) == 2
    # Should cancel unfinished task1
    assert experiment.get_n_tasks(registered_participant, finished=True) == 1
    assert experiment.get_n_tasks(registered_participant, canceled=True) == 1

    with pytest.raises(NoTasksAvailable):
        experiment.start_task(registered_participant)


def test_experiment_is_available_visible(registered_participant, experiment):
    assert experiment.is_available(registered_participant) is True

    experiment.visible = False
    experiment.save()
    assert experiment.is_available(registered_participant) is False


def test_experiment_is_available_requirements(registered_participant, experiment):
    assert experiment.is_available(registered_participant) is True

    required_experiment = Experiment.objects.create(visible=True)
    experiment.required_experiments.add(required_experiment)
    # Still available because required experiment has no assignments
    assert experiment.is_available(registered_participant) is True
    assert required_experiment.is_available(registered_participant) is True

    TaskAssignment.objects.create(
        participant=registered_participant,
        task=Task.objects.create(
            experiment=required_experiment,
            data={},
        ),
    )
    # No longer available because required experiments has unfinished assignments
    assert experiment.is_available(registered_participant) is False
    assert required_experiment.is_available(registered_participant) is True

    required_experiment.start_task(registered_participant)
    # Required experiment completed
    assert experiment.is_available(registered_participant) is True
    assert required_experiment.is_available(registered_participant) is True

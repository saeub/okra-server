import random
import string
import uuid
from functools import partial
from typing import Iterable, Optional

from django.db import models
from django.utils import timezone

from okra_server.exceptions import NoTasksAvailable


def _random_key(length: int):
    chars = string.ascii_letters + string.digits
    key = "".join(random.choice(chars) for _ in range(length))
    return key


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    device_key = models.CharField(max_length=24, null=True)
    registration_key = models.CharField(
        max_length=24, null=True, default=partial(_random_key, 24)
    )

    def __str__(self):
        registered = self.device_key is not None
        return (
            f'{"Registered" if registered else "Unregistered"} Participant "{self.id}"'
        )

    @property
    def experiments(self) -> models.QuerySet:
        experiments = Experiment.objects.filter(
            tasks__assignments__participant=self,
        ).distinct()
        return experiments

    def unregister(self):
        self.device_key = None
        self.registration_key = _random_key(24)

    def register(self):
        self.device_key = _random_key(24)
        self.registration_key = None


class TaskType(models.TextChoices):
    CLOZE = "cloze", "Cloze test"
    LEXICAL_DECISION = "lexical-decision", "Lexical decision"
    N_BACK = "n-back", "n-back"
    PICTURE_NAMING = "picture-naming", "Picture-naming"
    QUESTION_ANSWERING = "question-answering", "Question answering"
    REACTION_TIME = "reaction-time", "Reaction time"


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    task_type = models.CharField(max_length=50, choices=TaskType.choices)
    title = models.CharField(max_length=100)
    cover_image_url = models.URLField(null=True)
    instructions = models.TextField()
    practice_task = models.OneToOneField(
        "Task",
        null=True,
        on_delete=models.SET_NULL,
        related_name="practice_experiment",
    )

    def __str__(self):
        return f'Experiment "{self.title}" ({self.task_type})'

    def get_assignments(self, participant: Participant) -> Iterable["TaskAssignment"]:
        return TaskAssignment.objects.filter(
            task__in=self.tasks.all(),
            participant=participant,
        )

    def get_n_tasks(self, participant: Participant) -> int:
        return self.get_assignments(participant).count()

    def get_n_tasks_done(self, participant: Participant) -> int:
        return (
            self.get_assignments(participant)
            .filter(
                started_time__isnull=False,
            )
            .count()
        )

    def start_task(self, participant: Participant, practice: bool = False) -> "Task":
        # Cancel previously started and unfinished assignments
        canceled_assignments = TaskAssignment.objects.filter(
            participant=participant,
            started_time__isnull=False,
            finished_time__isnull=True,
        )
        for assignment in canceled_assignments:
            assignment.finish(None)
        if practice:
            assignment = TaskAssignment.objects.create(
                participant=participant,
                task=self.practice_task,
            )
        else:
            assignment = TaskAssignment.objects.filter(
                task__experiment=self,
                participant=participant,
                started_time__isnull=True,
            ).first()
        if assignment is None:
            raise NoTasksAvailable()
        assignment.start()
        return assignment.task


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    label = models.CharField(max_length=50, blank=True)
    experiment = models.ForeignKey(
        Experiment,
        null=True,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    data = models.JSONField()

    def __str__(self):
        return f'Task "{self.id}" of {self.experiment}'

    def finish(self, participant: Participant, results: Optional[dict]):
        self.assignments.get(
            participant=participant,
            finished_time__isnull=True,
        ).finish(results)


class TaskAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    results = models.JSONField(null=True)
    started_time = models.DateTimeField(null=True)
    finished_time = models.DateTimeField(null=True)

    class Meta:
        ordering = ["id"]

    def start(self):
        self.started_time = timezone.now()
        self.save()

    def finish(self, results: dict):
        self.results = results
        self.finished_time = timezone.now()
        self.save()

    def __str__(self):
        return f"Assignment of {self.task} to {self.participant}"


class TaskRatingType(models.TextChoices):
    EMOTICON = "emoticon", "Emoticons (right-positive)"
    EMOTICON_REVERSED = "emoticon-reversed", "Emoticons (left-positive)"
    RADIO = "radio", "Radio buttons"
    SLIDER = "slider", "Slider"


class TaskRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    question = models.TextField()
    rating_type = models.CharField(
        max_length=50,
        choices=TaskRatingType.choices,
    )
    low_extreme = models.TextField(null=True)
    high_extreme = models.TextField(null=True)

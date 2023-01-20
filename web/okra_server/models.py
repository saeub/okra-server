import random
import string
import uuid
from functools import partial
from typing import Optional

from django.db import models
from django.utils import timezone

from okra_server.exceptions import NoTasksAvailable


def _random_key(length: int):
    chars = string.ascii_letters + string.digits
    key = "".join(random.choice(chars) for _ in range(length))
    return key


new_registration_key = partial(_random_key, 24)


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    label = models.CharField(max_length=50, default="unlabeled", blank=True)
    device_key = models.CharField(max_length=24, null=True)
    registration_key = models.CharField(
        max_length=24, null=True, default=new_registration_key
    )

    class Meta:
        ordering = ["label"]

    def __str__(self):
        registered = self.device_key is not None
        return (
            f'{"Registered" if registered else "Unregistered"} Participant "{self.id}"'
        )

    @property
    def experiments(self) -> models.QuerySet["Experiment"]:
        experiments = Experiment.objects.filter(
            tasks__assignments__participant=self,
        ).distinct()
        return experiments

    def unregister(self, registration_key: Optional[str] = None):
        self.device_key = None
        self.registration_key = registration_key or new_registration_key()

    def register(self):
        self.device_key = _random_key(24)
        self.registration_key = None


class TaskType(models.TextChoices):
    CLOZE = "cloze", "Cloze test"
    DIGIT_SPAN = "digit-span", "Digit span"
    LEXICAL_DECISION = "lexical-decision", "Lexical decision"
    N_BACK = "n-back", "n-back"
    PICTURE_NAMING = "picture-naming", "Picture-naming"
    QUESTION_ANSWERING = "question-answering", "Question answering"
    REACTION_TIME = "reaction-time", "Reaction time"
    READING = "reading", "Reading"
    SIMON_GAME = "simon-game", "Simon game"
    TRAIL_MAKING = "trail-making", "Trail making"


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    task_type = models.CharField(max_length=50, choices=TaskType.choices)
    title = models.CharField(max_length=100)
    cover_image_url = models.URLField(null=True)
    instructions = models.TextField()
    instructions_after_task = models.TextField(null=True)
    instructions_after_practice_task = models.TextField(null=True)
    instructions_after_final_task = models.TextField(null=True)
    practice_task = models.OneToOneField(
        "Task",
        null=True,
        on_delete=models.SET_NULL,
        related_name="practice_experiment",
    )
    required_experiments = models.ManyToManyField(
        "self",
        related_name="requiring_experiments",
    )
    active = models.BooleanField(default=False)

    def __str__(self):
        return f'Experiment "{self.title}" ({self.task_type})'

    def get_assignments(
        self, participant: Participant, practice: bool = False
    ) -> models.QuerySet["TaskAssignment"]:
        if practice:
            assignments = TaskAssignment.objects.filter(
                task=self.practice_task,
                participant=participant,
            )
        else:
            assignments = TaskAssignment.objects.filter(
                task__in=self.tasks.all(),
                participant=participant,
            )
        return assignments

    def get_n_tasks(
        self,
        participant: Participant,
        practice: bool = False,
        started: Optional[bool] = None,
        finished: Optional[bool] = None,
        canceled: Optional[bool] = None,
    ) -> int:
        assignments = self.get_assignments(participant, practice=practice)

        if started is not None:
            assignments = assignments.filter(started_time__isnull=False)
        if finished is not None:
            assignments = assignments.filter(finished_time__isnull=not finished)
        if canceled is not None:
            assignments = assignments.filter(canceled=canceled)

        return assignments.count()

    def is_available(self, participant: Participant) -> bool:
        if not self.active:
            return False
        for experiment in self.required_experiments.all():
            if experiment.get_n_tasks(
                participant, started=True
            ) < experiment.get_n_tasks(participant):
                return False
        return True

    def start_task(self, participant: Participant, practice: bool = False) -> "Task":
        # Cancel previously started and unfinished assignments
        canceled_assignments = TaskAssignment.objects.filter(
            participant=participant,
            started_time__isnull=False,
            finished_time__isnull=True,
        )
        for assignment in canceled_assignments:
            assignment.cancel()
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
    data = models.JSONField(null=True)

    def __str__(self):
        if self.experiment is None:
            return f'Practice task "{self.id}" of {self.practice_experiment}'
        return f'Task "{self.id}" of {self.experiment}'

    @property
    def is_practice(self) -> bool:
        try:
            self.practice_experiment
            return True
        except Experiment.DoesNotExist:
            return False

    def finish(self, participant: Participant, results: Optional[dict]):
        self.assignments.get(
            participant=participant,
            finished_time__isnull=True,
        ).finish(results)

    def cancel(self, participant: Participant):
        self.assignments.get(
            participant=participant,
            finished_time__isnull=True,
        ).cancel()


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
    canceled = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def start(self):
        self.started_time = timezone.now()
        self.save()

    def finish(self, results: dict):
        self.results = results
        self.finished_time = timezone.now()
        self.save()

    def cancel(self):
        self.finished_time = timezone.now()
        self.canceled = True
        self.save()

    def __str__(self):
        return f"Assignment of {self.task} to {self.participant}"


class TaskRatingType(models.TextChoices):
    EMOTICON = "emoticon", "Emoticons (right-positive)"
    EMOTICON_REVERSED = "emoticon-reversed", "Emoticons (left-positive)"
    RADIO = "radio", "Radio buttons"
    RADIO_VERTICAL = "radio-vertical", "Radio buttons (vertical)"
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

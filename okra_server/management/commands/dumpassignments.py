import json

from django.core.management import BaseCommand, CommandParser

from okra_server.models import Participant, TaskAssignment


class Command(BaseCommand):
    help = "Dump assignments in JSON format"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--participant", "-p", help="Participant ID")

    def handle(self, *args, **options):
        assignments = TaskAssignment.objects.all()
        if options["participant"] is not None:
            participant = Participant.objects.get(id=options["participant"])
            assignments = assignments.filter(participant=participant)
        for assignment in assignments:
            print(
                json.dumps(
                    {
                        "assignmentId": str(assignment.id),
                        "participantId": str(assignment.participant.id),
                        "taskId": str(assignment.task.id),
                        "startedTime": (
                            assignment.started_time.isoformat()
                            if assignment.started_time is not None
                            else None
                        ),
                        "finishedTime": (
                            assignment.finished_time.isoformat()
                            if assignment.finished_time is not None
                            else None
                        ),
                        "results": assignment.results,
                    }
                )
            )

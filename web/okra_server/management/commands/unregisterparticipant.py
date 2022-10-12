from django.core.management import BaseCommand, CommandParser

from okra_server.models import Participant


class Command(BaseCommand):
    help = "Unregister a participant and generate a new registration key"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("participant", help="Participant ID")
        parser.add_argument(
            "--registration-key",
            "-k",
            help="New registration key",
        )

    def handle(self, *args, **options):
        participant = Participant.objects.get(id=options["participant"])
        participant.unregister(options["registration_key"])
        participant.save()
        print(participant.registration_key)

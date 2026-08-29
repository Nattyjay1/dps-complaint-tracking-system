from django.core.management.base import BaseCommand

from complaints.services import ensure_default_statuses


class Command(BaseCommand):
    help = "Create the default complaint statuses."

    def handle(self, *args, **options):
        ensure_default_statuses()
        self.stdout.write(self.style.SUCCESS("Default statuses are ready."))

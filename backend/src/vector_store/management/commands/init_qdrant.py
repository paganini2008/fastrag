from django.core.management.base import BaseCommand
from config.container import container


class Command(BaseCommand):
    help = "Initialize Qdrant collection with payload indexes"

    def handle(self, *args, **options):
        vs = container.vector_store()
        vs.ensure_collection()
        self.stdout.write(self.style.SUCCESS("Qdrant collection initialized."))

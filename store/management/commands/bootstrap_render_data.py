from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command

from orders.models import Order
from store.models import Category, Flavor


class Command(BaseCommand):
    help = "Load the exported fixture into a fresh Render/Postgres database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Load the fixture even if data already exists.",
        )

    def handle(self, *args, **options):
        fixture_path = Path("data/render_seed.json")
        if not fixture_path.exists():
            self.stdout.write("No render fixture found. Skipping bootstrap data load.")
            return

        has_data = (
            get_user_model().objects.exists()
            or Category.objects.exists()
            or Flavor.objects.exists()
            or Order.objects.exists()
        )
        if has_data and not options["force"]:
            self.stdout.write("Database already contains data. Skipping bootstrap data load.")
            return

        call_command("loaddata", str(fixture_path))
        self.stdout.write(self.style.SUCCESS("Render bootstrap data loaded successfully."))

from django.core.management import call_command
from django.test import TestCase

from store.models import Flavor


class SeedDataTests(TestCase):
    def test_seed_data_adds_a_richer_catalog(self):
        call_command('seed_data')

        self.assertGreaterEqual(Flavor.objects.count(), 16)
        self.assertTrue(Flavor.objects.exclude(image_url='').exists())

from django.db import migrations


OLD_IMAGE_URLS = [
    'https://images.unsplash.com/photo-1505253716362-afaea1a3d1af?auto=format&fit=crop&q=80&w=600',
    'https://unsplash.com/photos/vanilla-ice-cream-with-berry-swirl-dIs-MqalSSE',
]
NEW_IMAGE_URL = 'https://images.unsplash.com/photo-1597249536924-b226b1a1259d?auto=format&fit=crop&q=80&w=600'


def update_cinnamon_image(apps, schema_editor):
    Flavor = apps.get_model('store', 'Flavor')
    Flavor.objects.filter(
        name='Cinnamon Swirl Crunch',
        image_url__in=OLD_IMAGE_URLS,
    ).update(image_url=NEW_IMAGE_URL)


def restore_cinnamon_image(apps, schema_editor):
    Flavor = apps.get_model('store', 'Flavor')
    Flavor.objects.filter(
        name='Cinnamon Swirl Crunch',
        image_url=NEW_IMAGE_URL,
    ).update(image_url=OLD_IMAGE_URLS[0])


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0003_seed_default_catalog'),
    ]

    operations = [
        migrations.RunPython(update_cinnamon_image, restore_cinnamon_image),
    ]

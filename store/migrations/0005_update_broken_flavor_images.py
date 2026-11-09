from django.db import migrations


FLAVOR_IMAGE_UPDATES = {
    'Black Sesame Midnight': (
        'https://images.unsplash.com/photo-1563699902328-8b82f9929c8e?auto=format&fit=crop&q=80&w=600',
        'https://images.unsplash.com/photo-1715194803865-54f4358f87ef?auto=format&fit=crop&q=80&w=600',
    ),
    'Blueberry Ripple': (
        'https://images.unsplash.com/photo-1519996521430-02b4d6cb0af4?auto=format&fit=crop&q=80&w=600',
        'https://images.unsplash.com/photo-1627222295124-f8b3fc09e47f?auto=format&fit=crop&q=80&w=600',
    ),
}


def update_broken_images(apps, schema_editor):
    Flavor = apps.get_model('store', 'Flavor')
    for name, (old_url, new_url) in FLAVOR_IMAGE_UPDATES.items():
        Flavor.objects.filter(name=name, image_url=old_url).update(image_url=new_url)


def restore_broken_images(apps, schema_editor):
    Flavor = apps.get_model('store', 'Flavor')
    for name, (old_url, new_url) in FLAVOR_IMAGE_UPDATES.items():
        Flavor.objects.filter(name=name, image_url=new_url).update(image_url=old_url)


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0004_update_cinnamon_swirl_image'),
    ]

    operations = [
        migrations.RunPython(update_broken_images, restore_broken_images),
    ]

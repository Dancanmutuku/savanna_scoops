from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], default='info', max_length=20)),
                ('logger_name', models.CharField(db_index=True, max_length=150)),
                ('message', models.TextField()),
                ('module', models.CharField(blank=True, max_length=100)),
                ('function', models.CharField(blank=True, max_length=100)),
                ('path', models.CharField(blank=True, max_length=300)),
                ('traceback', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

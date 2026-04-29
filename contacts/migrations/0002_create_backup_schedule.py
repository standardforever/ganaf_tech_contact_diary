from django.db import migrations
import json


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    from django.conf import settings
    interval_hours = getattr(settings, 'BACKUP_INTERVAL_HOURS', 24)

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=interval_hours,
        period='hours',  # use the string directly instead of IntervalSchedule.HOURS
    )

    PeriodicTask.objects.get_or_create(
        name='Auto DB Backup',
        defaults={
            'interval': schedule,
            'task': 'contacts.tasks.auto_backup',
            'args': json.dumps([]),
        }
    )

def delete_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name='Auto DB Backup').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('django_celery_beat', '0018_improve_crontab_helptext'),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, delete_periodic_task),
    ]
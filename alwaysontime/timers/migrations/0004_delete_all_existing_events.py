# Generated by Django 4.0 on 2021-12-21 16:02

from django.db import migrations


def delete_all_existing_events(apps, schema_editor):
    Event = apps.get_model('timers', 'Event')
    db_alias = schema_editor.connection.alias
    Event.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('timers', '0003_event_calendar'),
    ]

    operations = [
        migrations.RunPython(delete_all_existing_events)
    ]
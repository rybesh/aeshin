# Generated by Django 4.2.4 on 2023-08-15 21:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0031_building_remove_course_recitations_course_room_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="milestone",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
# Generated by Django 5.1.4 on 2025-01-08 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0039_externalcourse_alter_course_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalcourse",
            name="subtitle",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
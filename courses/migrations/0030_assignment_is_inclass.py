# Generated by Django 4.2.4 on 2023-08-15 14:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0029_remove_peerreviewsession_assignment_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="is_inclass",
            field=models.BooleanField(default=False, verbose_name="given in class"),
        ),
    ]

# Generated by Django 5.0.1 on 2024-01-09 19:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0035_meeting_powerpoint"),
    ]

    operations = [
        migrations.CreateModel(
            name="Viewing",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.TextField()),
                ("tips", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="ViewingAssignment",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("order", models.IntegerField(blank=True, null=True)),
                ("is_optional", models.BooleanField(default=False)),
                (
                    "meeting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="viewing_assignments",
                        to="courses.meeting",
                    ),
                ),
                (
                    "viewing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="courses.viewing",
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
            },
        ),
        migrations.AddField(
            model_name="meeting",
            name="viewings",
            field=models.ManyToManyField(
                blank=True, through="courses.ViewingAssignment", to="courses.viewing"
            ),
        ),
        migrations.CreateModel(
            name="ViewingPart",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.PositiveSmallIntegerField()),
                ("minutes", models.PositiveSmallIntegerField()),
                ("url", models.URLField()),
                (
                    "viewing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parts",
                        to="courses.viewing",
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
            },
        ),
    ]

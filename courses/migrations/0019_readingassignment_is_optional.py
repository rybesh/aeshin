# Generated by Django 3.1 on 2020-08-06 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_auto_20200319_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='readingassignment',
            name='is_optional',
            field=models.BooleanField(default=False),
        ),
    ]

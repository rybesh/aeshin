# Generated by Django 3.1.4 on 2021-01-07 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0023_delete_readingsummary'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_weekly',
            field=models.BooleanField(default=False),
        ),
    ]

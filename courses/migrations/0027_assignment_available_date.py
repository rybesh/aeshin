# Generated by Django 3.1.4 on 2021-01-07 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0026_auto_20210107_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='available_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
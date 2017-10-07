# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import courses.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField()),
                ('due_date', models.DateField(blank=True)),
                ('title', models.CharField(max_length=80)),
                ('description', models.TextField()),
                ('points', models.IntegerField(default=0)),
                ('is_handed_out', models.BooleanField(default=False)),
                ('is_submitted_online', models.BooleanField(default=False)),
                ('is_letter_graded', models.BooleanField(default=False)),
                ('is_graded', models.BooleanField(default=False, verbose_name=b'has been graded')),
            ],
            options={
                'ordering': ('due_date', 'slug'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=20)),
                ('slug', models.CharField(max_length=20)),
                ('title', models.CharField(max_length=80)),
                ('semester', models.CharField(max_length=2, choices=[(b'sp', b'Spring'), (b'fa', b'Fall')])),
                ('year', models.IntegerField(choices=[(2011, b'2011'), (2012, b'2012'), (2013, b'2013'), (2014, b'2014'), (2015, b'2015'), (2016, b'2016')])),
                ('times', models.CharField(max_length=64)),
                ('location', models.CharField(max_length=32)),
                ('ereserves_id', models.CharField(max_length=8, blank=True)),
                ('description', models.TextField()),
                ('blurb', models.TextField(blank=True)),
                ('evaluation', models.TextField(blank=True)),
                ('participation', models.TextField(blank=True)),
                ('thanks', models.TextField(blank=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('blog_slug', models.CharField(max_length=20, blank=True)),
                ('forum', models.URLField(blank=True)),
            ],
            options={
                'ordering': ('-year', 'semester'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=80)),
                ('course', models.ForeignKey(related_name='holidays', to='courses.Course')),
            ],
            options={
                'ordering': ('date',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=36)),
                ('url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('title', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('is_tentative', models.BooleanField(default=True)),
                ('slides', models.FileField(null=True, upload_to=courses.models.upload_to, blank=True)),
                ('course', models.ForeignKey(related_name='meetings', to='courses.Course')),
            ],
            options={
                'ordering': ('course', 'date'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reading',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('zotero_id', models.CharField(max_length=16)),
                ('citation_text', models.CharField(max_length=128, editable=False, blank=True)),
                ('citation_html', models.TextField(editable=False, blank=True)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to=b'courses/readings', blank=True)),
                ('url', models.URLField(blank=True)),
                ('access_via_proxy', models.BooleanField(default=False)),
                ('access_via_ereserves', models.BooleanField(default=False)),
                ('ignore_citation_url', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('citation_text',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReadingAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('discussion_questions', models.TextField(blank=True)),
                ('discussion_leader', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('meeting', models.ForeignKey(related_name='reading_assignments', to='courses.Meeting')),
                ('reading', models.ForeignKey(to='courses.Reading')),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_submitted', models.DateTimeField()),
                ('zipfile', models.FileField(upload_to=courses.models.submission_upload_to, blank=True)),
                ('grade', models.FloatField(default=0.0)),
                ('letter_grade', models.CharField(max_length=2, blank=True)),
                ('comments', models.TextField(blank=True)),
                ('assignment', models.ForeignKey(related_name='submissions', to='courses.Assignment')),
                ('submitter', models.ForeignKey(related_name='submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='meeting',
            name='readings',
            field=models.ManyToManyField(to='courses.Reading', through='courses.ReadingAssignment', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='assistant',
            field=models.ForeignKey(related_name='courses_assisting', blank=True, to='courses.Instructor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='department',
            field=models.ForeignKey(related_name='courses', to='courses.Department'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='instructor',
            field=models.ForeignKey(related_name='courses', to='courses.Instructor'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(related_name='courses', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('slug', 'semester', 'year')]),
        ),
        migrations.AddField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(related_name='assignments', to='courses.Course'),
            preserve_default=True,
        ),
    ]

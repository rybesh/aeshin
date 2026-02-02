#!/bin/sh
python manage.py migrate --noinput
gunicorn --bind :8000 aeshin.wsgi

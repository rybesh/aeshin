FROM ghcr.io/benoitc/gunicorn:25

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

RUN apt-get update && apt-get install -y \
    libmagic1 \
    rsync \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

COPY . /code/

# dummy environment variables so collectstatic can run
ENV SECRET_KEY "dummy-secret-key"
ENV DATABASE_URL "sqlite:///dummy-database-url"
ENV EMAIL_HOST_USER "dummy-email-host-user"
ENV EMAIL_HOST_PASSWORD "dummy-email-host-password"

RUN python manage.py collectstatic --noinput

EXPOSE 8000

COPY ./entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

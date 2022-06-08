#!/bin/bash

cd /app/src/

poetry install
poetry run python manage.py collectstatic --noinput
poetry run python manage.py migrate --noinput
supervisorctl start celery-worker
poetry run uwsgi --master --http 0.0.0.0:8000 \
--module atlassian_addon.wsgi:application

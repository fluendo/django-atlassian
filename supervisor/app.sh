#!/bin/bash

cd /app/src/

poetry install
poetry run python manage.py collectstatic
poetry run python manage.py migrate
poetry run uwsgi --master --http 0.0.0.0:8000 \
--module atlassian_addon.wsgi:application

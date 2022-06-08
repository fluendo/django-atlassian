#!/bin/bash

cd /app/src/
sleep 10
poetry run celery -A atlassian_addon.celery worker -l INFO

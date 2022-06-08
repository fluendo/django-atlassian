#!/bin/bash

cd /app/src/

poetry run celery -A atlassian_addon.celery worker -l INFO

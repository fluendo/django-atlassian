#!/usr/bin/env bash

# database
export DB_NAME="atlassian_addon"
export DB_USER="fluendo"
export DB_PASSWD="---"
export DB_HOST="fluendo-stage-01.cpb7g9t0u127.us-east-1.rds.amazonaws.com"

# django & python
export DJANGO_SETTINGS_MODULE='fluendo.settings.dev'
export DJANGO_DEBUG=True
export PYTHONUNBUFFERED=True

# Jira & Issue static server tokens
export JIRA_SERVER='https://fluendo-dev.atlassian.net/'
export JIRA_USER='aburgos@fluendo.com'
export JIRA_TOKEN='---'

# fluendo
export FLUENDO_BASE_ADMIN_URL='https://stage.fluendo.com/en/admin/'
export WEB_FLUENDO_API_SERVER='https://stage.fluendo.com/en/api/'
export WEB_FLUENDO_TOKEN='---'

# atlassian
export URL_BASE='https://atlassian-addon-dev.fluendo.com/'

# runme
cd /home/ubuntu/atlassian-addon-dev/atlassian-addon
exec /home/ubuntu/atlassian-addon-dev/pyenv-dev/bin/gunicorn \
fluendo.wsgi:application \
--bind unix:/tmp/atlassian_addon_dev.sock \
--log-level debug

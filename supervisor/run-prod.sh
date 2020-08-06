#!/usr/bin/env bash

# database
export DB_NAME="atlassian_addon"
export DB_USER="fluendo"
export DB_PASSWD="xxxxx"
export DB_HOST="fluendo-prod.cpb7g9t0u127.us-east-1.rds.amazonaws.com"

# django & python
export DJANGO_SETTINGS_MODULE='fluendo.settings.prod'
export DJANGO_DEBUG=True
export PYTHONUNBUFFERED=True

# Jira & Issue static server tokens
export JIRA_SERVER='https://fluendo.atlassian.net/'
export JIRA_USER='fluendo-sys@fluendo.com'
export JIRA_TOKEN='xxxxx'

# fluendo API
export WEB_FLUENDO_API_SERVER='https://fluendo.com/en/api/'
export WEB_FLUENDO_TOKEN='xxxxx'

# atlassian
export URL_BASE='https://atlassian.fluendo.com/'

# runme
cd /home/ubuntu/atlassian-addon-prod/atlassian-addon
exec /home/ubuntu/atlassian-addon-prod/pyenv-prod/bin/gunicorn \
atlassian_addon.wsgi:application \
--bind unix:/tmp/atlassian_addon_prod.sock \
--log-level debug -w 4

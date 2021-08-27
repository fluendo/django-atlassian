#!/usr/bin/env bash

# celery
source /home/ubuntu/atlassian-addon-prod/export-env
cd /home/ubuntu/atlassian-addon-prod/atlassian-addon
exec /home/ubuntu/atlassian-addon-prod/pyenv-prod/bin/celery -A atlassian_addon worker -B -l INFO


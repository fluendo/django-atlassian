from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlassian_addon.settings.dev")

app = Celery("atlassian_addon")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

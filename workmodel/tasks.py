# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import logging

from jira import JIRA
from celery import shared_task
from django_atlassian.models.connect import SecurityContext
from django.utils import dateparse

from workmodel.views import search_issues
from workmodel.services import WorkmodelService

@shared_task
def update_issue_business_time(sc_id, issue_key):
    sc = SecurityContext.objects.get(id=sc_id)
    wm = WorkmodelService()
    wm.business_time.business_time(issue_key)


@shared_task
def update_issues_business_time(sc_id):
    sc = SecurityContext.objects.get(id=sc_id)
    wm = WorkmodelService(sc)
    wm.business_time.update_all_business_time(update_issues_business_time.request.id)


@shared_task
def update_in_progress_business_time(sc_id):
    sc = SecurityContext.objects.get(id=sc_id)
    wm = WorkmodelService(sc)
    wm.business_time.update_in_progress_business_time()

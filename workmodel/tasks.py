# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import logging

from jira import JIRA
from celery import shared_task
from django_atlassian.models.connect import SecurityContext
from django.utils import dateparse

from workmodel.views import search_issues, get_issue_hierarchy

logger = logging.getLogger('workmodel_logger')


def transition_to_days(from_transition, to_transition):
    fromDate = from_transition['created']
    toDate = to_transition['created']
    # Get the timespan
    daygenerator = (fromDate + datetime.timedelta(x + 1) for x in range((toDate - fromDate).days))
    # Remove non working days
    days = sum(1 for day in daygenerator if day.weekday() < 5)
    return days


def calculate_task_business_time(jira, issue):
    statuses = jira.statuses()
    transitions = []
    for h in issue.changelog.histories:
        # Get all transitions
        created = dateparse.parse_datetime(h.created).date()
        for item in h.items:
            if item.field == 'status':
                # Get transitions where the from status is of "In Progress" category
                # Get transitions where the to status is of "In Progress" category
                # Warning: We have duplicate names for statuses
                fromCategory = toCategory = None
                for s in statuses:
                    if fromCategory and toCategory:
                        break
                    if s.name == item.fromString:
                        fromCategory = s.statusCategory.name
                    if s.name == item.toString:
                        toCategory = s.statusCategory.name
                if fromCategory != 'In Progress' and toCategory != 'In Progress':
                    continue
                # Always keep it sorted from oldest to newer
                transitions.insert(0, {'created': created, 'fromCategory': fromCategory, 'toCategory': toCategory})
    if not transitions:
        days = 0
    else:
        days = 1
        # In case the task is currently in progress, create a fake transition
        if transitions[len(transitions) - 1]['toCategory'] == 'In Progress':
            transitions.append({'created': datetime.date.today(), 'fromCategory': 'In Progress', 'toCategory': 'Done'})
        for i in range(1, len(transitions)):
            # Skip transitions that happened in the same day
            if transitions[i-1]['created'] == transitions[i]['created']:
                continue
            # Sum every filtered timespan
            days += transition_to_days(transitions[i-1], transitions[i])
    return days


def calculate_epic_business_time(jira, issue):
    # We can not use parenEpic as it also returns the same issue and sub-tasks
    # whoes parent belongs to an Epic
    issues = search_issues(jira, "'Epic Link' = {}".format(issue.key), expand='changelog')
    days = 0
    for issue in issues:
        days += calculate_issue_business_time(jira, issue)
    return days


def calculate_initiative_business_time(jira, issue):
    issues = search_issues(jira, "issue in linkedIssues({0}, 'contains')".format(issue.key), expand='changelog')
    days = 0
    for issue in issues:
        days += calculate_issue_business_time(jira, issue)
    return days


def calculate_issue_business_time(jira, issue):
    logger.debug("Calculating spent time for {}".format(issue.key))
    if issue.fields.issuetype.name in ('Task', 'Bug', 'Activity', 'Story'):
        days = calculate_task_business_time(jira, issue)
    elif issue.fields.issuetype.name in ('Epic'): 
        days = calculate_epic_business_time(jira, issue)
    elif issue.fields.issuetype.name in ('Initiative'): 
        days = calculate_initiative_business_time(jira, issue)
    else:
        logger.debug("Unknown issue type {}".format(issue.fields.issuetype.name))
        days = 0
    logger.debug("Total spent time for {} is {} days".format(issue.key, days))
    # Store the information as a property
    jira.add_issue_property(issue.key, "transitions", { 'progress_summation': days })
    # TODO keep track of the modification time
    return days


@shared_task
def update_issue_business_time(sc_id, issue_key):
    sc = SecurityContext.objects.get(id=sc_id)
    jira = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    issue = jira.issue(issue_key, expand='changelog')
    calculate_issue_business_time(jira, issue)


@shared_task
def update_issues_business_time(sc_id):
    sc = SecurityContext.objects.get(id=sc_id)
    logger.info("Updating all issues")
    jira = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    issues = search_issues(jira, "", expand='changelog')
    for issue in issues:
        calculate_issue_business_time(jira, issue)
    # Remove the addon task id
    prop = None
    props = jira.app_properties(sc.key)
    for p in props:
        if p.key == 'workmodel-configuration':
            prop = p
            break
    prop.update({'task_id': None})

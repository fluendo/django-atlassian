# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import atlassian_jwt
from urlparse import urlparse
from jira import JIRA
import datetime

from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django_atlassian.decorators import jwt_required
from django_atlassian.models.connect import SecurityContext
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from fluendo.proxy_api import customers_proxy_cache

@csrf_exempt
@jwt_required
@xframe_options_exempt
def customers_view(request):
    sc = request.atlassian_sc
    key = request.GET.get('key')
    property_key = 'customers'
    customers_json = None

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    customers = customers_proxy_cache(request)
    customers_json = json.loads(customers.content)
    try:
        p = j.issue_property(key, property_key)
        customer = p.value.customer
        customer_id = p.value.customer_id
    except:
        customer = 'Click to choose one'
        customer_id = 0

    customer_property = {
        'value': {
            'customer': customer,
            'customer_id': customer_id
        }
    }

    # Encode the update URL to make a secure call to ourselves
    url = "{}?key={}".format(reverse('workmodel-customers-view-update'), key)
    token = atlassian_jwt.encode_token('POST', url, sc.client_key, sc.shared_secret)

    return render(
        request,
        'workmodel/customers_view.html',
        {
            'key': key,
            'jwt': token,
            'customers': customers_json,
            'c_property': customer_property,
        }
    )


@xframe_options_exempt
def customers_proxy_view(request):
    return customers_proxy_cache(request)


@csrf_protect
@jwt_required
def customers_view_update(request):
    sc = request.atlassian_sc
    key = request.GET.get('key')
    property_key = 'customers'
    data = json.loads(request.body)
    customer = data['customer']
    customer_id = data['customer_id']

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    j.add_issue_property(key, property_key, {'customer': customer, 'customer_id': customer_id })
    return HttpResponse(status=200)


def search_issues(j, jql, expand=None):
    start_at = 0
    result = []
    while True:
        r = j.search_issues(jql, startAt=start_at, expand=expand)
        total = len(r)
        if total == 0:
            break
        result += r
        start_at += total

    return result


def get_child_issues(j, key, relation='contains', extra_jql=None):
    """
    Function to get the issues on a hierarchy of issues
    """
    jql = "issue in linkedIssues({0}, {1}) "\
        "OR parent in linkedIssues({0}, {1}) "\
        "OR parentEpic in linkedIssues({0}, {1})"\
        .format(key, relation)
    if extra_jql:
        jql = "({0}) {1}".format(jql, extra_jql)

    return get_issues(j, jql)


def get_issues_progress(issues):
    """
    For a list of issues, get the corresponding status categories as absolute
    values and relative to the total
    """
    total = len(issues)
    todo = progress = done = 0
    todo_pt = progress_pt = done_pt = 0
    if total != 0:
        for i in issues:
            if i.fields.status.statusCategory.name == 'Done':
                done = done + 1
            elif i.fields.status.statusCategory.name == 'To Do':
                todo = todo + 1
            elif i.fields.status.statusCategory.name == 'In Progress':
                progress = progress + 1
        todo_pt = int(float(todo) / total * 100)
        progress_pt = int(float(progress) / total * 100)
        done_pt = int(float(done) / total * 100)
    return {
        'total': total,
        'todo': todo,
        'todo_pt': todo_pt,
        'progress': progress,
        'progress_pt': progress_pt,
        'done': done,
        'done_pt': done_pt,
    }


@xframe_options_exempt
@jwt_required
def initiative_status(request):
    # Mandatory parameters
    key = request.GET.get('initiativeKey')
    # Get the security context from the same jira instance
    sc = request.atlassian_sc
    parsed_uri = urlparse(sc.host)
    jira_host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    sc = SecurityContext.objects.filter(host=jira_host, key=request.atlassian_sc.key, product_type='jira').get()
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    issues = get_child_issues(j, key)
    summary = get_issues_progress(issues)
    return render(
        request,
        'workmodel/initiative_status.html',
        summary
    )


@xframe_options_exempt
@jwt_required
def issue_versions(request):
    # Mandatory parameters
    key = request.GET.get('issueKey')
    # Get the security context from the same jira instance
    sc = request.atlassian_sc
    parsed_uri = urlparse(sc.host)
    jira_host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    sc = SecurityContext.objects.filter(host=jira_host, key=request.atlassian_sc.key, product_type='jira').get()
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})

    issues = get_child_issues(j, key)
    versions = {}
    for i in issues:
        for v in i.fields.fixVersions:
            if not v in versions:
                versions[v.name] = {}
                # Get the summary asynchronous
                versions[v.name]['projects'] = []
                # Encode the update URL to make a secure call to ourselves
                url = "{}?issueKey={}&fixVersion={}".format(reverse('workmodel-issue-versions-progress'), key, v.name)
                token = atlassian_jwt.encode_token('GET', url, sc.client_key, sc.shared_secret)
                versions[v.name]['progress'] = "{}://{}{}&jwt={}".format(request.scheme, request.get_host(), url, token) 
            p = {
                'project': i.fields.project.key,
                'url': '{0}/browse/{1}/fixforversion/{2}'.format(jira_host, i.fields.project.key, v.id),
                'status': "released" if v.released else "unreleased"
            }
            versions[v.name]['projects'] = versions[v.name]['projects'] + [p]
    return render(
        request,
        'workmodel/issue_versions.html',
        {'data': versions}
    )

@xframe_options_exempt
@jwt_required
def issue_versions_progress(request):
    # Mandatory parameters
    key = request.GET.get('issueKey')
    version = request.GET.get('fixVersion')
    # Get the security context from the same jira instance
    sc = request.atlassian_sc
    parsed_uri = urlparse(sc.host)
    jira_host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    sc = SecurityContext.objects.filter(host=jira_host, key=request.atlassian_sc.key, product_type='jira').get()
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    issues = get_child_issues(j, key, extra_jql="AND fixVersion IN ('{0}')".format(version))
    summary = get_issues_progress(issues)
    return render(
        request,
        'workmodel/initiative_status.html',
        summary
    )


@csrf_exempt
@jwt_required
def addon_enabled(request):
    sc = request.atlassian_sc
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    field_name = 'com.fluendo.atlassian-addon__workmodel-affected-products-field'
    options = j.custom_field_options_app(field_name)
    projects = j.projects()
    options_ids = [option.properties.id for option in options]
    for project in projects:
        properties = { 'name': project.name, 'key': project.key, 'id': project.id }
        # Create the option based on the project id
        if not project.id in options_ids:
            j.create_custom_field_option_app(
                field_name,
                project.name,
                properties
            )
        # Update the options in case the project name or key have changed
        else:
            option = [option for option in options if option.properties.id == project.id][0]
            option.update(value=project.name, id=option.id, properties=properties)
    # Confirm that there's already a schedule every day
    schedule, created = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)
    # Confirm that there's already a job that rescans every issue
    if not PeriodicTask.objects.filter(args=json.dumps(['security_context.id', sc.id])).count():
        PeriodicTask.objects.create(
            interval=schedule, name="Update In-Progress business time",
            task='workmodel.tasks.update_in_progress_business_time',
            args=json.dumps(['security_context.id', sc.id]),
        )
    return HttpResponse(204)


@csrf_exempt
@jwt_required
def project_created(request):
    sc = request.atlassian_sc
    data = json.loads(request.body)
    project = data['project']
    properties = { 'name': project['name'], 'key': project['key'], 'id': str(project['id']) }
    field_name = 'com.fluendo.atlassian-addon__workmodel-affected-products-field'

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    j.create_custom_field_option_app(field_name, project['name'], properties)
    return HttpResponse(204)


@csrf_exempt
@jwt_required
def project_updated(request):
    sc = request.atlassian_sc
    data = json.loads(request.body)
    project = data['project']
    properties = { 'name': project['name'], 'key': project['key'], 'id': str(project['id']) }
    field_name = 'com.fluendo.atlassian-addon__workmodel-affected-products-field'

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    options = j.custom_field_options_app(field_name)
    option = [option for option in options if option.properties.id == str(project['id'])][0]
    option.update(value=project['name'], id=option.id, properties=properties)
    return HttpResponse(204)


@csrf_exempt
@jwt_required
def project_deleted(request):
    sc = request.atlassian_sc
    data = json.loads(request.body)
    project = data['project']
    field_name = 'com.fluendo.atlassian-addon__workmodel-affected-products-field'

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    options = j.custom_field_options_app(field_name)
    option = [option for option in options if option.properties.id == str(project['id'])][0]
    option.delete()
    return HttpResponse(204)


def get_issue_hierarchy(j, issue_key):
    # Get the Epic
    i = j.issue(issue_key)
    epic_field = [x for x in j.fields() if 'Epic Link' == x['name']][0]['key']
    epic_key = getattr(i.fields, epic_field)
    if epic_key:
        # Get the initiative
        epic = j.issue(epic_key)
        initiative_key = None
        for il in epic.fields.issuelinks:
            if il.type.name == 'Contains':
                initiative_key = il.inwardIssue.key
                break
        if initiative_key:
            return initiative_key
        else:
            return epic_key
    else:
        return issue_key


@csrf_exempt
@jwt_required
def issue_updated(request):
    sc = request.atlassian_sc
    data = json.loads(request.body)
    issue = data['issue']
    changelog = data['changelog']

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    to_update = []
    # Check a hierarchy change and trigger the corresponding job
    for item in changelog['items']:
        # In case the issue has been transitioned
        if item['field'] == 'status':
            # Update ourselves or the whole hierarchy
            to_update.append(get_issue_hierarchy(j, issue['key']))
        elif item['field'] == 'Link':
            from_issue = parse.parse("This issue contains {}", item['fromString'])
            if from_issue:
                # Update ourselves
                to_update.append(issue['key'])
            from_issue = parse.parse("This issue is contained in {}", item['fromString'])
            if from_issue:
                # Update other
                to_update.append(from_issue)
            to_issue = parse.parse("This issue contains {}", item['toString'])
            if to_issue:
                # Update ourselves
                to_update.append(issue['key'])
            to_issue = parse.parse("This issue is contained in {}", item['toString'])
            if to_issue:
                # Update other
                to_update.append(from_issue)
        elif item['field'] == 'Epic Link':
            if item['fromString']:
                # Update other
                to_update.append(item['fromString'])
            if item['toString']:
                # Update other
                to_update.append(item['fromString'])
        elif item['field'] == 'Epic Child':
            if item['fromString']:
                # Update ourselves
                to_update.append(issue['key'])
            if item['toString']:
                # Update ourselves
                to_update.append(issue['key'])
    # Uniquify the list
    to_update = list(set(to_update))
    # Create a task to update each progress
    from workmodel.tasks import update_issue_business_time
    for u in to_update:
        print("Updating business time for {}".format(u))
        update_issue_business_time.delay(sc.id, u)
    return HttpResponse(204)


def get_jira_default_configuration(j, sc):
    # default configuration
    conf = {
        'hierarchy': None,
        'task_id': None,
        'version': 1,
    }
    # already created configuration
    props = j.app_properties(sc.key)
    for p in props:
        if p.key == 'workmodel-configuration':
            conf = {}
            if hasattr(p.value, 'task_id'):
                conf['task_id'] = p.value.task_id
            else:
                conf['task_id'] = None
            if hasattr(p.value, 'hierarchy'):
                conf['hierarchy'] = p.raw['value']['hierarchy']
            else:
                conf['hierarchy'] = None
            if hasattr(p.value, 'version'):
                conf['version'] = p.value.version
            else:
                conf['version'] = 1
    # Create the app configuration in case it is not there yet
    j.create_app_property(sc.key, 'workmodel-configuration', conf)
    return conf


@xframe_options_exempt
@jwt_required
def jira_configuration(request):
    # Get the addon configuration
    sc = request.atlassian_sc
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    # Encode the update URL to make a secure call to ourselves
    url = reverse('workmodel-configuration-update-issues-business-time')
    token = atlassian_jwt.encode_token('POST', url, sc.client_key, sc.shared_secret)
    conf = get_jira_default_configuration(j, sc)
    return render(request, 'workmodel/jira_configuration.html', {
        'update_issues_url': url,
        'update_issues_url_jwt': token,
        'conf': conf
    })


@xframe_options_exempt
@jwt_required
def issues_hierarchy_configuration(request):
    sc = request.atlassian_sc
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    # Get the current configuration
    conf = get_jira_default_configuration(j, sc)
    # Replace the ids with actual values
    issue_types = j.issue_types()
    resolved_hierarchies = []
    for h in conf['hierarchy']:
        hierarchy = h
        h['issues'] = [i for i in issue_types if i.id in h['issues']]
        resolved_hierarchies.append(h)
    conf['hierarchy'] = resolved_hierarchies
    return render(request, 'workmodel/issues_hierarchy_configuration.html', {
        'issue_types': issue_types,
        'fields': j.fields(),
        'issue_link_types': j.issue_link_types(),
        'conf': conf
    })


@csrf_exempt
@jwt_required
def configuration_update_issues_business_time(request):
    sc = request.atlassian_sc
    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    # We assume there is already a configuration stored
    prop = None
    props = j.app_properties(sc.key)
    for p in props:
        if p.key == 'workmodel-configuration':
            prop = p
            break
    from workmodel.tasks import update_issues_business_time
    res = update_issues_business_time.delay(sc.id)
    prop.update({'task_id': res.task_id})
    return HttpResponse(204)

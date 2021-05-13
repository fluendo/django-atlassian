# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import atlassian_jwt
from urlparse import urlparse
from jira import JIRA

from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django_atlassian.decorators import jwt_required
from django_atlassian.models.connect import SecurityContext

from workmodel.models import Issue
from fluendo.proxy_api import customers_proxy_cache

def labels_update_labels(i, to_add, to_remove):
    update = False
    for l in to_add:
        if l not in i.labels:
            i.labels.append(l)
            update = True
    for l in to_remove:
        if l in i.labels:
            i.labels.remove(l)
            update = True
    if update:
        print "Updating labels to"
        i.save()


def labels_set_parent_labels(i):
    parent = i.get_parent()
    if parent:
        to_add = parent.labels
        labels_update_labels(i, to_add, [])


def labels_issue_created(i):
    if i.has_parent():
        labels_set_parent_labels(i)


def labels_issue_updated(i, changelog):
    # Check what has changed
    for item in changelog['items']:
        # In case the labels have changed
        if item['field'] == 'labels':
            # In case is a parent, we need to add/remove the labels
            # in every children
            if is_parent(i):
                from_labels = item['fromString'].split(" ")
                to_labels = item['toString'].split(" ")
                to_add = [x for x in to_labels if x not in from_labels]
                to_remove = [x for x in from_labels if x not in to_labels]
                for children in i.get_children():
                    labels_update_labels(children, to_add, to_remove)
            # In case the labels have been updated, make sure to keep
            # the parents labels too
            if i.has_parent():
                labels_set_parent_labels(i)


@csrf_exempt
@jwt_required
def issue_updated(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    changelog = body['changelog']
    labels_issue_updated(i, changelog)
    return HttpResponse(204)


@csrf_exempt
@jwt_required
def issue_created(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    labels_issue_created(i)
    return HttpResponse(204)

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
    url = "{}?key={}".format(reverse('customers-view-update'), key)
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

    start_at = 0
    result = []
    while True:
        r = j.search_issues(jql, startAt=start_at)
        total = len(r)
        if total == 0:
            break
        result += r
        start_at += total

    return result


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


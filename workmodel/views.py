# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import atlassian_jwt
from urlparse import urlparse
from jira import JIRA
import datetime
from dateutil.relativedelta import relativedelta

from django.forms import formset_factory
from django.urls import reverse
from django.utils import dateparse
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django_atlassian.decorators import jwt_required, jwt_qsh_exempt
from django_atlassian.models.connect import SecurityContext
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from workmodel.services import WorkmodelService
from workmodel.forms import HierarchyForm

def get_issues_progress(issues):
    """
    For a generator of issues, get the corresponding status categories as absolute
    values and relative to the total
    """
    total = 0
    todo = progress = done = 0
    todo_pt = progress_pt = done_pt = 0
    for i in issues:
        if i.fields.status.statusCategory.name == 'Done':
            done = done + 1
        elif i.fields.status.statusCategory.name == 'To Do':
            todo = todo + 1
        elif i.fields.status.statusCategory.name == 'In Progress':
            progress = progress + 1
        total = total + 1
    if total != 0:
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
    wm = WorkmodelService(sc)
    issues = wm.hierarchy.child_issues(key)
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
    wm = WorkmodelService(sc)
    issues = wm.hierarchy.child_issues(key)
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
    wm = WorkmodelService(sc)
    issues = wm.hierarchy.child_issues(key, extra_jql="AND fixVersion IN ('{0}')".format(version))
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


@csrf_exempt
@jwt_required
def issue_updated(request):
    sc = request.atlassian_sc
    data = json.loads(request.body)
    issue = data['issue']
    changelog = data['changelog']
    to_update = []
    # Check a hierarchy change and trigger the corresponding job
    for item in changelog['items']:
        # In case the issue has been transitioned
        if item['field'] == 'status':
            wm = WorkmodelService(sc)
            # Update ourselves or the whole hierarchy
            try:
                root = wm.hierarchy.root_issue(issue['key'])
                to_update.append(root.key)
            except:
                # nothing to do
                pass
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
        update_issue_business_time.delay(sc.id, u)
    return HttpResponse(204)


@xframe_options_exempt
@jwt_required
@jwt_qsh_exempt
def business_time_transitions_dashboard_item_configuration(request):
    sc = request.atlassian_sc
    # mandatory
    dashboard_id = request.GET.get('dashboardId', None)
    item_id = request.GET.get('dashboardItemId', None)
    # non mandatory
    filter_id = request.GET.get('filterId', None)

    wm = WorkmodelService(sc, account_id=request.atlassian_account_id)
    # Check if we are saving the configuration or rendering only
    if filter_id:
        # Save the property
        wm.jira.create_dashboard_item_property(dashboard_id, item_id,
                'business-time-transitions-configuration', filter_id)
        # Redirect to render
        url = "{}?dashboardId={}&dashboardItemId={}".format(
                reverse('workmodel-business-time-transitions-dashboard-item'),
                dashboard_id,
                item_id
        )
        token = sc.create_token('GET', url, account=request.atlassian_account_id)
        url = "{}&jwt={}".format(url, token)
        return redirect(url)
    else:
        filters = wm.search_filters()
        return render(
            request,
            'workmodel/transitions_dashboard_item_configuration.html',
            {
                'dashboardId': dashboard_id,
                'dashboardItemId': item_id,
                'filters': filters,
            }
        )


@xframe_options_exempt
@jwt_required
def business_time_transitions_dashboard_item(request):
    sc = request.atlassian_sc
    # mandatory
    dashboard_id = request.GET.get('dashboardId', None)
    item_id = request.GET.get('dashboardItemId', None)

    wm = WorkmodelService(sc, account_id=request.atlassian_account_id)
    # Check if we have a configuration, otherwise render the configuration page
    try:
        conf = wm.jira.dashboard_item_property(dashboard_id, item_id,
                "business-time-transitions-configuration")
    except:
        filters = wm.search_filters()
        # Redirect to conf
        url = "{}?dashboardId={}&dashboardItemId={}".format(
                reverse('workmodel-business-time-transitions-dashboard-item-configuration'),
                dashboard_id,
                item_id
        )
        token = sc.create_token('GET', url, account=request.atlassian_account_id)
        url = "{}&jwt={}".format(url, token)
        return redirect(url)

    # Get the issues associated with such filter id
    f = wm.jira.filter(conf.value)
    # Current year span
    today = datetime.date.today()
    year_start = datetime.date(today.year, 1, 1)
    year_end = datetime.date(today.year, 12, 31)
    delta = year_end - year_start
    days = delta.days + 1

    # Get the configuration
    conf = wm.business_time.conf

    # Prepare the data for plotting
    data = []
    count = 0
    for i in wm.search_issues(f.jql):
        # Get the transitions
        try:
            transitions = wm.jira.issue_property(i, 'transitions')
        except:
            continue
        row = {'issue': i, 'start': None, 'end': None}
        # Get the start/end fields
        if conf.value.start_field_id and conf.value.end_field_id:
            start = getattr(i.fields, conf.value.start_field_id, None)
            end = getattr(i.fields, conf.value.end_field_id, None)
            if start and end:
                start = dateparse.parse_date(start)
                if start < year_start:
                    start = year_start
                if start > year_end:
                    start = year_end
                row['start'] = start.timetuple().tm_yday

                end = dateparse.parse_date(end)
                if end > year_end:
                    end = year_end
                if end < year_start:
                    end = year_start
                row['end'] = end.timetuple().tm_yday
        ts = []
        try:
            for s in transitions.value.statuses:
                # Clip to current year only
                from_date = dateparse.parse_date(s.from_date)
                if from_date < year_start:
                    from_date = year_start
                if from_date > year_end:
                    from_date = year_end

                to_date = dateparse.parse_date(s.to_date)
                if to_date > year_end:
                    to_date = year_end
                if to_date < year_start:
                    to_date = year_start

                x1 = from_date.timetuple().tm_yday
                x2 = to_date.timetuple().tm_yday
                if s.status == 'None':
                    color = 'red'
                elif s.status == 'In Progress':
                    color = 'blue'
                elif s.status == 'To Do':
                    color = 'grey'
                elif s.status == 'Done':
                    color = 'green'
                t = {
                    'x': x1,
                    'width': x2 - x1,
                    'from': from_date,
                    'to': to_date,
                    'dur': to_date - from_date,
                    'color': color
                }
                ts.append(t)
        except AttributeError:
            continue
        row['transitions'] = ts
        count += 1
        data.append(row)

    months = []
    for m in range(1, 13):
        day_first = datetime.date(today.year, m, 1)
        day_last = day_first + relativedelta(months=1) - relativedelta(days=1)
        name = datetime.datetime.combine(day_first, datetime.datetime.min.time()).strftime("%b")
        month = {
            'name': name,
            'x1': day_first.timetuple().tm_yday,
            'x2': day_last.timetuple().tm_yday,
            'from': day_first,
            'to': day_last,
        }
        months.append(month)

    quarters = []
    for q in range(1, 5):
        day_first = datetime.date(today.year, ((q-1)*3)+1, 1)
        day_last = day_first + relativedelta(months=3) - relativedelta(days=1)
        quarter = {
            'name': 'Q{}'.format(q),
            'x1': day_first.timetuple().tm_yday,
            'x2': day_last.timetuple().tm_yday,
            'from': day_first,
            'to': day_last,
        }
        quarters.append(quarter)
        
    return render(
        request,
        'workmodel/transitions_dashboard_item.html',
        {
            'dashboardId': dashboard_id,
            'dashboardItemId': item_id,
            'data': data,
            'months': months,
            'quarters': quarters,
            'year': today.year,
            'sc': sc,
        }
    )


@xframe_options_exempt
@jwt_required
def business_time_configuration(request):
    # Get the addon configuration
    sc = request.atlassian_sc
    wm = WorkmodelService(sc)
    conf = wm.business_time.conf
    fields = [f for f in wm.jira.fields() if 'schema' in f and f['schema']['type'] in ['date', 'datetime']]
    fields.sort(key=lambda field: field['name'])
    return render(request, 'workmodel/business_time_configuration.html', {
        'conf': conf,
        'fields': fields,
    })


@csrf_exempt
@jwt_required
@jwt_qsh_exempt
def business_time_rescan_issues_progress(request):
    from workmodel.tasks import update_issues_business_time
    sc = request.atlassian_sc
    update_issues_business_time.delay(sc.id)
    url = reverse('workmodel-business-time-configuration')
    token = sc.create_token('GET', url, account=request.atlassian_account_id)
    url = "{}?jwt={}".format(url, token)
    return redirect(url)


@csrf_exempt
@jwt_required
@jwt_qsh_exempt
def business_time_update_start_stop_fields(request):
    # Update the configuration
    sc = request.atlassian_sc
    wm = WorkmodelService(sc)
    val = wm.business_time.conf.raw['value']
    val['start_field_id'] = request.GET.get('startId', None)
    val['end_field_id'] = request.GET.get('endId', None)
    wm.business_time.conf.update(val)
    # Redirect
    url = reverse('workmodel-business-time-configuration')
    token = sc.create_token('GET', url, account=request.atlassian_account_id)
    url = "{}?jwt={}".format(url, token)
    return redirect(url)


@xframe_options_exempt
@jwt_required
def hierarchy_configuration(request):
    sc = request.atlassian_sc
    wm = WorkmodelService(sc)
    # Create the formset
    HierarchyFormSet = formset_factory(HierarchyForm, can_order=True, can_delete=True, extra=0)
    formset = HierarchyFormSet(
        form_kwargs={'hierarchy_service': wm.hierarchy},
        initial=wm.hierarchy.conf.raw['value']['hierarchy']
    )
    return render(request, 'workmodel/hierarchy_configuration2.html', {
        'formset': formset,
    })


@xframe_options_exempt
@jwt_required
@jwt_qsh_exempt
def hierarchy_update_configuration(request):
    sc = request.atlassian_sc
    wm = WorkmodelService(sc)

    HierarchyFormSet = formset_factory(HierarchyForm, can_order=True, can_delete=True, extra=0)
    formset = HierarchyFormSet(request.GET,
        form_kwargs={'hierarchy_service': wm.hierarchy}
    )

    if formset.is_valid():
        hierarchy = []
        for form in formset.ordered_forms:
            if form.cleaned_data['DELETE']:
                continue
            hierarchy_level = {
                'is_container': form.cleaned_data['is_container'],
                'field': form.cleaned_data['field'],
                'link': form.cleaned_data['link'],
                'is_operative': form.cleaned_data['is_operative'],
                'type': form.cleaned_data['type'],
                'issues': form.cleaned_data['issues'],
            }
            hierarchy.append(hierarchy_level)
        # Update the configuration
        val = wm.hierarchy.conf.raw['value']
        val['hierarchy'] = hierarchy
        wm.hierarchy.conf.update(val)

    url = reverse('workmodel-hierarchy-configuration')
    token = sc.create_token('GET', url, account=request.atlassian_account_id)
    url = "{}?jwt={}".format(url, token)
    return redirect(url)

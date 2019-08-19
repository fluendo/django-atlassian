# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
import operator

from django.db import connections
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.http import JsonResponse

from django_atlassian.decorators import jwt_required

from models import Issue

# For initiative to epic relationships create a linkedtype of "Belongs to" or something similar. Store it as a global configuration.
# Create a entitytype property searchable for that, then on JQL we can say parentStatus = 'Done' o better parentResolved
# For dates, we can use start date and due date, start date is part of a plugin so we might let the user choose what fields


# Create a jiraprojectPages for configuring the project to show:
# The desired issue type to use
# The desired linkedIssueType to use
# Store that information as an entity property on the project
# Read the configuration of the project (entity property) to autoselect the information
# Reference to AUI https://docs.atlassian.com/aui/7.9.9/
#  


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
def postfunction_increment_create(request, workflow_conf=None):
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.get_internal_type() == 'FloatField':
            numeric_fields.append(f)
        if f.name == workflow_conf:
            field = f
    data = {
        'fields': numeric_fields,
        'field': field
    }
    return render(request, 'increment_create.html', data)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def postfunction_increment_view(request, workflow_conf=None):
    # get the verbose name from the field
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.name == workflow_conf:
            field = f
            break

    return render(request, 'increment_view.html', {'field': field})


@csrf_exempt
@jwt_required
def postfunction_increment_triggered(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    field = body['configuration']['value']
    try:
        value = getattr(i, field)
        if not value:
            value = 0
        value = value + 1
        setattr(i, field, value)
        i.save(update_fields=[field])
    except:
        return HttpResponseBadRequest()
    return HttpResponse(204)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def postfunction_decrement_create(request, workflow_conf=None):
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.get_internal_type() == 'FloatField':
            numeric_fields.append(f)
        if f.name == workflow_conf:
            field = f
    data = {
        'fields': numeric_fields,
        'field': field
    }
    return render(request, 'decrement_create.html', data)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def postfunction_decrement_view(request, workflow_conf=None):
    # get the verbose name from the field
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.name == workflow_conf:
            field = f
            break

    return render(request, 'decrement_view.html', {'field': field})


@csrf_exempt
@jwt_required
def postfunction_decrement_triggered(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    field = body['configuration']['value']
    try:
        value = getattr(i, field)
        if not value:
            value = 0
        value = value - 1
        if value < 0:
            value = 0
        setattr(i, field, value)
        i.save(update_fields=[field])
    except:
        return HttpResponseBadRequest()
    return HttpResponse(204)

@csrf_exempt
@jwt_required
@xframe_options_exempt
def customers_view(request):
    Issue = request.atlassian_model
    key = request.GET.get('key')
    property_key = 'customers'
    issue = None
    customers_json = None

    if key:
        issue = Issue.objects.get(key=key)
    
    customers = customers_proxy_cache(request)
    if customers:
        customers_json = json.loads(customers.content)

    if key and issue and customers:
        try:
            customer_property = Issue.jira.issue_property(
                issue, property_key)
        except:
            customer_property = {
                'value':{
                    'customer': 'click to choose one',
                    'customer_id': 0,
                }
            }

        rest_url = '/rest/api/2/issue/' + issue.key + '/properties/customers'
        return render(
            request,
            'customers_view.html',
            {
                'issue': issue,
                'rest_url': rest_url,
                'customers': customers_json,
                'c_property': customer_property,
            })
    else:
        return HttpResponseBadRequest()

@csrf_protect
def customers_view_update(request):
    try:
        Issue = request.atlassian_model
    except:
        from atlassian.models import Issue

    issue_key = request.GET.get('issue_key')
    property_key = 'customers'
    issue = None
    data = json.loads(request.body)
    customer = data['customer']
    customer_id = data['customer_id']

    if issue_key:
        issue = Issue.objects.get(key=issue_key)
        Issue.jira.add_issue_property(
            issue_key,
            property_key,
            {
                'customer': customer,
                'customer_id': customer_id
            }
        )

    return HttpResponse(status=200)

# Cache time to live is 15 minutes.
CACHE_TTL = 60 * 15
@cache_page(CACHE_TTL)
def customers_proxy_cache(request):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customers/'
    r = requests.get(api_url, headers=web_auth)
    data = sorted(r.json(), key=operator.itemgetter('company_name'))
    return JsonResponse(data, safe=False)

@xframe_options_exempt
def customers_proxy_view(request):
    return customers_proxy_cache(request)

@xframe_options_exempt
def helloworld(request):
    return render(request, 'helloworld.html')


class AppDescriptor(TemplateView):
    template_name = 'atlassian-connect.json'
    content_type = 'application/json'

    def get_context_data(self, *args, **kwargs):
        context = super(AppDescriptor, self).get_context_data(*args, **kwargs)
        base_url = self.request.build_absolute_uri('/')
        context['base_url'] = getattr(settings, 'URL_BASE', base_url)
        return context


class SalesCustomersView(View):
    template_name = 'sales-customers-view.html'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        customers = customers_proxy_cache(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'customers': json.loads(customers.content)}
        )
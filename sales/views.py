# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
import operator

from django.db import connections
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
from django.views.generic import CreateView
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.http import JsonResponse, Http404
from django.contrib import messages

from django_atlassian.decorators import jwt_required

from atlassian.models import Issue

from customers.proxy_api import (
    agreements_by_account_id,
    customer_by_id_proxy,
    customers_proxy_cache,
    contact_by_id_proxy,
    contacts_proxy,
    contact_proxy_patch,
    account_contacts_by_pk,
    user_proxy,
    patch_account
)

from sales.forms import (
    AccountForm,
    ContactForm
)


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


@xframe_options_exempt
def helloworld(request):
    return render(request, 'fluendo.html')


class AppDescriptor(TemplateView):
    template_name = 'atlassian-connect.json'
    content_type = 'application/json'

    def get_context_data(self, *args, **kwargs):
        context = super(AppDescriptor, self).get_context_data(*args, **kwargs)
        base_url = self.request.build_absolute_uri('/')
        context['base_url'] = getattr(settings, 'URL_BASE', base_url)
        return context


class SalesAccountsListView(View):
    template_name = 'sales/accounts-list-view.html'

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        accounts = customers_proxy_cache(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'accounts': json.loads(accounts.content)}
        )


class SalesAccountDetailView(View):
    template_name = 'sales/account-detail.html'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            account_json = customer_by_id_proxy(request, account_pk)
            account = json.loads(account_json.content)
            
            agreements = []
            for agreement_pk in account['reselleragreement_set']:
                agreements_json = agreements_by_account_id(request, agreement_pk)
                agreements += [json.loads(agreements_json.content)]

            contacts = []
            for contact_pk in account['customercontact_set']:
                contacts_json = account_contacts_by_pk(request,contact_pk)
                contacts += [json.loads(contacts_json.content)]

            account_form = AccountForm(initial=account)
            fluendo = settings.FLUENDO

            return render(
                request,
                self.template_name,
                {
                    'account_form': account_form,
                    'account': account,
                    'agreements': agreements,
                    'contacts': contacts,
                    'fluendo': fluendo,
                }
            )
        else:
            raise Http404()
    
    @method_decorator(xframe_options_exempt, csrf_protect)
    def post(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            form = AccountForm(
                data=request.POST,
                initial=request.POST)
            if form.is_valid():
                form.fix_boolean_fields()
                json_data = form.cleaned_data
                response = patch_account(account_pk, json_data)
                if response.status_code == 200:
                        messages.success(
                            request,
                            str(response.status_code) + ': OK' #+ response.text
                        )
                else:
                    messages.warning(
                        request,
                        str(response.status_code) + ': ' + response.text
                    )
            else:
                messages.error('form data error')
                return redirect('sales-account-detail-view', pk=account_pk)
        else:
            return Http404()
        return redirect('sales-account-detail-view', pk=account_pk)


class SalesContactsListView(View):
    template_name = 'sales/contact-list-view.html'

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        contacts = contacts_proxy(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'contacts': json.loads(contacts.content)}
        )


class SalesContactsDetailView(View):
    template_name = "sales/contact-detail-view.html"
    form_class = ContactForm

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        contact_pk = kwargs.get('pk', None)

        if contact_pk:
            contact_json = contact_by_id_proxy(request, contact_pk)
            contact = json.loads(contact_json.content) 
            return render(
                request,
                self.template_name,
                {
                    'form': self.form_class(initial=contact),
                }
            )
        else:
            raise Http404()
            
    @method_decorator(xframe_options_exempt, jwt_required)
    def post(self, request, *args, **kwargs):
        contact_pk = kwargs.get('pk', None) 
        form = self.form_class(request.POST)
        if contact_pk:
            if form.is_valid():
                contact_json = json.dumps(form.cleaned_data)
                response = contact_proxy_patch(contact_pk, contact_json)
                if response.status_code == 200:
                    messages.success(
                        request,
                        str(response.status_code) + ': OK' #+ response.text
                    )
                else:
                    messages.warning(
                        request,
                        str(response.status_code) + ': ' + response.content
                    )
            else:
                messages.error(request, str(form.errors))
        else:
            raise Http404()
        return redirect('sales-contacts-detail-view', pk=contact_pk)


class SalesContactsAddView(CreateView):
    template_name = "sales/contact-add-view.html"
    form_class = ContactForm


    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {
                'form': self.form_class()
            }

        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            contact_data = json.dumps(form.cleaned_data)
            response = contacts_proxy_post(contact_data)
            if response.status_code == 204:
               messages.success(
                   request,
                   str(response.status_code) + ': Created' #+ response.text
               )
            else:
               messages.warning(
                   request,
                   str(response.status_code) + ': ' + response.reason_phrase
               )
        else:
            messages.error(request, str(form.errors))
            return render(
                        request,
                        self.template_name,
                        {
                            'form': self.form_class()
                        }
            )
        return redirect('sales-contacts-list-view')


class SalesUsersSearch(View):

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        return user_proxy(search)
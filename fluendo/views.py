# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from jira import JIRA

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django_atlassian.decorators import jwt_required

from fluendo.proxy_api import (
    customers_proxy_cache,
    company_proxy_cache
)


def get_jira(sc):
    return JIRA(
        sc.host,
        jwt={
            'secret': sc.shared_secret,
            'payload': {
                'iss': sc.key
            }
        }
    )


@csrf_exempt
@jwt_required
@xframe_options_exempt
def customers_view(request):
    sc = request.atlassian_sc
    key = request.GET.get('key')
    property_key = 'customers'

    j = get_jira(sc)
    customers = customers_proxy_cache(request)
    try:
        p = j.issue_property(key, property_key)
        customer_id = int(p.value.customer_id)
    except:
        customer_id = None

    return render(
        request,
        'fluendo/customers_view.html',
        {
            'key': key,
            'customers': json.loads(customers.content),
            'customer': customer_id,
        }
    )


@xframe_options_exempt
def customers_proxy_view(request):
    return customers_proxy_cache(request)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def company_view(request):
    sc = request.atlassian_sc
    key = request.GET.get('key')
    property_key = 'companies'

    jira = get_jira(sc)
    company = company_proxy_cache(request)

    try:
        p = jira.issue_property(key, property_key)
        company_name = p.value.company
        company_id = int(p.value.company_id)
    except:
        company_name = None
        company_id = None

    return render(
        request,
        'fluendo/company_view.html',
        {
            'key': key,
            'companies': json.loads(company.content),
            'company': company_name,
            'company_id': company_id,
        }
    )


@xframe_options_exempt
def company_proxy_view(request):
    return company_proxy_cache(request)

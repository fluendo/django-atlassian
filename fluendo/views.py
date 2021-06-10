# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from jira import JIRA
import atlassian_jwt

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django_atlassian.decorators import jwt_required
from django_atlassian.models.connect import SecurityContext

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
    try:
        p = j.issue_property(key, property_key)
        customer_id = p.value.customer_id
    except:
        customer_id = None

    return render(
        request,
        'fluendo/customers_view.html',
        {
            'key': key,
            'customers': json.loads(customers.content),
            'customer': int(customer_id),
        }
    )


@xframe_options_exempt
def customers_proxy_view(request):
    return customers_proxy_cache(request)

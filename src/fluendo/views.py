# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django_atlassian.decorators import jwt_required

from fluendo.proxy_api import company_proxy_cache, customers_proxy_cache
from jira import JIRA


def get_jira(sc):
    return JIRA(sc.host, jwt={"secret": sc.shared_secret, "payload": {"iss": sc.key}})


@csrf_exempt
@jwt_required
@xframe_options_exempt
def company_view(request):
    sc = request.atlassian_sc
    key = request.GET.get("key")
    property_key = "companies"

    jira = get_jira(sc)
    company = company_proxy_cache(request)

    return render(
        request,
        "fluendo/company_view.html",
        {
            "key": key,
            "companies": json.loads(company.content),
        },
    )


@xframe_options_exempt
def company_proxy_view(request):
    return company_proxy_cache(request)

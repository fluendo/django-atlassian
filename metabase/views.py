# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import jwt
import time

from jira import JIRA
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django_atlassian.decorators import jwt_required
from django_atlassian.models.connect import SecurityContext

@xframe_options_exempt
@jwt_required
def configuration(request):
    return render(
        request,
        'metabase/configuration.html')


@xframe_options_exempt
@jwt_required
def dashboard_item_view(request):
    sc = request.atlassian_sc
    # non mandatory
    dashboard_id = request.GET.get('dashboardId', None)
    item_id = request.GET.get('dashboardItemId', None)
    # mandatory
    view = request.GET.get('view')

    j = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
    properties = j.app_properties('com.fluendo.atlassian-addon')
    configuration = [p for p in j.app_properties('com.fluendo.atlassian-addon') if p.key == 'metabase-configuration']

    if not configuration:
        return render(
            request,
            'metabase/dashboard_item_missing_configuration.html'
        )
    iframe_url = ""
    if dashboard_id and item_id:
        try:
            prop = j.dashboard_item_property(dashboard_id, item_id, 'metabase-configuration')
            if hasattr(prop.value.payload.resource, 'question'):
                resource = 'question'
            else:
                resource = 'dashboard'
            payload = {
              "resource": {
                  resource: getattr(prop.value.payload.resource, resource)
              },
              "params": {
              },
              "exp": round(time.time()) + (60 * 10) # 10 minute expiration
            }
            token = jwt.encode(payload, configuration[0].value.token, algorithm="HS256")
            iframe_url = "{}/embed/{}/{}#bordered={}&titled={}&theme={}".format(
                configuration[0].value.url,
                resource,
                token.decode("utf8"),
                str(prop.value.border).lower(),
                str(prop.value.title).lower(),
                prop.value.theme
            )
        except:
          pass
    return render(
        request,
        'metabase/dashboard_item.html',
        {
            'dashboard': dashboard_id,
            'dashboardItem': item_id,
            'iframe_url': iframe_url
        }
    )

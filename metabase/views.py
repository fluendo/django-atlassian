# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import jwt
import time
import atlassian_jwt
from jira import JIRA
import requests


from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django_atlassian.decorators import jwt_required
from django_atlassian.models.connect import SecurityContext

from metabase.models import MetabaseConfiguration

@xframe_options_exempt
@jwt_required
def jira_configuration(request):
    return render(
        request,
        'metabase/jira_configuration.html')


class ConfluenceConfiguration(View):
    http_method_names = ['get', 'post']

    @method_decorator(xframe_options_exempt)
    @method_decorator(jwt_required)
    def get(self, request):
        conf, created = MetabaseConfiguration.objects.get_or_create(account=request.atlassian_sc)
        if created:
          conf.save()
        return render(request, 'metabase/confluence_configuration.html', {'conf': conf})

    @method_decorator(xframe_options_exempt)
    def post(self, request):
        conf = MetabaseConfiguration.objects.get(id=request.POST.get('id'))
        conf.site_url = request.POST.get('site_url')
        conf.secret_key = request.POST.get('secret_key')
        conf.save()
        return render(request, 'metabase/confluence_configuration.html', {'conf': conf})


@xframe_options_exempt
@jwt_required
def macro_view(request):
    sc = request.atlassian_sc
    # mandatory arguments
    page_id = request.GET.get('pageId')
    page_version = request.GET.get('pageVersion')
    macro_id = request.GET.get('macroId')
    # Get the parameters from this macro
    url = '/rest/api/content/{}/history/{}/macro/id/{}'.format(page_id, page_version, macro_id)
    token = atlassian_jwt.encode_token('GET', url, sc.key, sc.shared_secret)
    url = "{}{}".format(sc.host, url)
    response = requests.get(url, headers={'Authorization': 'JWT {}'.format(token)})
    if response:
        try:
            conf = json.loads(response.json()['parameters']['data']['value'])
            if conf['payload']['resource'].has_key('question'):
                resource = 'question'
            else:
                resource = 'dashboard'
            conf['payload']['exp'] = round(time.time()) + (60 * 10) # 10 minute expiration
            mbconf = MetabaseConfiguration.objects.get(account=request.atlassian_sc)
            if not mbconf.site_url or not mbconf.secret_key:
                raise AttributeError

            token = jwt.encode(conf['payload'], mbconf.secret_key, algorithm="HS256")
            iframe_url = "{}/embed/{}/{}#bordered={}&titled={}&theme={}".format(
                mbconf.site_url,
                resource,
                token.decode("utf8"),
                str(conf['border']).lower(),
                str(conf['title']).lower(),
                conf['theme']
            )
        except Exception as e:
            return render(
                request,
                'metabase/confluence_wrong_configuration.html'
            )
    else:
        return render(
            request,
            'metabase/macro_missing.html'
        )
    return render(
        request,
        'metabase/macro_view.html',
        {
            'iframe_url': iframe_url
        })


@xframe_options_exempt
@jwt_required
def macro_configuration(request):
    return render(
        request,
        'metabase/macro_configuration.html',
    )


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
              "params": getattr(prop.value.payload, "params", {}),
              "exp": round(time.time()) + (60 * 10) # 10 minute expiration
            }
            token = jwt.encode(payload, configuration[0].value.secret_key, algorithm="HS256")
            iframe_url = "{}/embed/{}/{}#bordered={}&titled={}&theme={}".format(
                configuration[0].value.site_url,
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

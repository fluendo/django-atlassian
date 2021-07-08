# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from importlib import import_module
import json
import jwt

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.apps import apps
from django.views.generic.base import TemplateView
from django.core.exceptions import ImproperlyConfigured
from django.template import engines

from models.connect import SecurityContext

@csrf_exempt
def installed(request):
    """
    Main view to handle the signal of the cloud instance when the addon
    has been installed
    """
    try:
        post = json.loads(request.body)
        key = post['key']
        shared_secret = post['sharedSecret']
        client_key = post['clientKey']
        host = post['baseUrl']
        product_type = post['productType']
        oauth_client_id = post.get('oauthClientId')
    except MultiValueDictKeyError:
        return HttpResponseBadRequest()

    # Store the security context
    # https://developer.atlassian.com/cloud/jira/platform/authentication-for-apps/
    sc = SecurityContext.objects.filter(key=key, host=host).first()
    if sc:
        update = False
        # Confirm that the shared key is the same, otherwise update it
        if sc.shared_secret != shared_secret:
            sc.shared_secret = shared_secret
            update = True
        if sc.client_key != client_key:
            sc.client_key = client_key
            update = True
        if sc.oauth_client_id != oauth_client_id:
            sc.oauth_client_id = oauth_client_id
            update = True
        if update:
            sc.save()
    else:
        # Create a new entry on our database of connections
        sc = SecurityContext()
        sc.key = key
        sc.host = host
        sc.shared_secret = shared_secret
        sc.client_key = client_key
        sc.product_type = product_type
        sc.oauth_client_id = oauth_client_id
        sc.save()

    return HttpResponse(status=204)


class ApplicationDescriptor(TemplateView):
    content_type = 'application/json'

    def get_application_name(self):
        if self.application_name is None:
            raise ImproperlyConfigured(
                "ApplicationDescriptor requires a definition of 'application_name' "
                "or an implementation of 'get_application_name()'")
        return self.application_name

    def get_template_names(self):
        return ['django_atlassian/{}/atlassian-connect.json'.format(self.get_application_name())]

    def get_context_data(self, *args, **kwargs):
        context = super(ApplicationDescriptor, self).get_context_data(*args, **kwargs)
        base_url = self.request.build_absolute_uri('/')
        context['base_url'] = getattr(settings, 'URL_BASE', base_url)
        # Get all the contents of the registered apps application_name_modules.py files
        modules = {}
        for app in apps.get_app_configs():
            try:
                module = import_module('{}.{}_modules'.format(app.module.__name__, self.get_application_name()))
                for m in module.modules:
                    for k,v in m.items():
                        if not k in modules.keys():
                            modules[k] = []
                        modules[k] = modules[k] + v
            except ImportError:
                continue

        # Process the contents of the modules by the tenplate engine
        django_engine = engines['django']
        j = json.dumps(modules)
        j = "{% load staticfiles %} " + j
        template = django_engine.from_string(j)
        context['modules'] = template.render()
        # Get the needed settings or abort
        context['name'] = getattr(settings, 'DJANGO_ATLASSIAN_{}_NAME'.format(self.get_application_name().upper()))
        context['description'] = getattr(settings, 'DJANGO_ATLASSIAN_{}_DESCRIPTION'.format(self.get_application_name().upper()))
        context['key'] = getattr(settings, 'DJANGO_ATLASSIAN_{}_KEY'.format(self.get_application_name().upper()))
        context['vendor_name'] = getattr(settings, 'DJANGO_ATLASSIAN_VENDOR_NAME')
        context['vendor_url'] = getattr(settings, 'DJANGO_ATLASSIAN_VENDOR_URL')

        return context


class JiraDescriptor(ApplicationDescriptor):
    application_name = 'jira'


class ConfluenceDescriptor(ApplicationDescriptor):
    application_name = 'confluence'

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic.base import TemplateView

from django_atlassian.decorators import jwt_required

class AppDescriptor(TemplateView):
    template_name = 'confluence-connect.json'
    content_type = 'application/json'

    def get_context_data(self, *args, **kwargs):
        context = super(AppDescriptor, self).get_context_data(*args, **kwargs)
        base_url = self.request.build_absolute_uri('/')
        context['base_url'] = getattr(settings, 'URL_BASE', base_url)
        return context

@xframe_options_exempt
def helloworld(request):
    return render(request, 'helloworld.html')

@xframe_options_exempt
@jwt_required
def initiative_status(request):
    key = request.GET.get('key')
    # jql = issue in linkedIssues($key, contains) OR parent in linkedIssues($key, contains) OR parentEpic in linkedIssues($key, contains)
    # Get all the children issues, grouped by type, count how many
    # and finally pass the data
    return render(request, 'initiative-status.html')

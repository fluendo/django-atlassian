# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jira import JIRA
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic.base import TemplateView

from django_atlassian.decorators import jwt_required

class AppDescriptor(TemplateView):
    template_name = 'confluence/confluence-connect.json'
    content_type = 'application/json'

    def get_context_data(self, *args, **kwargs):
        context = super(AppDescriptor, self).get_context_data(*args, **kwargs)
        base_url = self.request.build_absolute_uri('/')
        context['base_url'] = getattr(settings, 'URL_BASE', base_url)
        return context

@xframe_options_exempt
def helloworld(request):
    return render(request, 'confluence/helloworld.html')

@xframe_options_exempt
@jwt_required
def initiative_status(request):
    key = request.GET.get('initiativeKey')
    # FIXME The confluence plugin does not have access to the JIRA instance (yet?)
    # so we instantiate
    # a new jira connection with the credentials found on the databases
    db = settings.DATABASES['jira']
    j = JIRA(db['NAME'], basic_auth=(db['USER'], db['PASSWORD']))
    r = j.search_issues(
        "issue in linkedIssues({0}, contains) "\
        "OR parent in linkedIssues({0}, contains) "\
        "OR parentEpic in linkedIssues({0}, contains)"\
        .format(key)
    )
    total = len(r)
    print(total)
    todo = progress = done = 0
    todo_pt = progress_pt = done_pt = 0
    if total != 0:
        for i in r:
            if i.fields.status.statusCategory.name == 'Done':
                done = done + 1
            elif i.fields.status.statusCategory.name == 'To Do':
                todo = todo + 1
            elif i.fields.status.statusCategory.name == 'In Progress':
                progress = progress + 1
        todo_pt = int(float(todo) / total * 100)
        progress_pt = int(float(progress) / total * 100)
        done_pt = int(float(done) / total * 100)
    return render(
        request,
        'confluence/initiative-status.html',
        {
            'total': total,
            'todo': todo,
            'todo_pt': todo_pt,
            'progress': progress,
            'progress_pt': progress_pt,
            'done': done,
            'done_pt': done_pt,
        }
    )

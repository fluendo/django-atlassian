# -*- coding: utf-8 -*-

import requests
import json

from django.db.models.manager import Manager
from django.conf import settings

class JiraManager(Manager):
    def __init__(self):
        super(JiraManager, self).__init__()
        # Get the jira database in order to do the requests
        for alias, db in settings.DATABASES.items():
            if db['ENGINE'] == 'django_atlassian.backends.jira':
                self.user = db['USER']
                self.token = db['PASSWORD']
                self.base_uri = db['NAME']

    def get_uri(self, endpoint):
        return '%s/%s' % (self.base_uri, endpoint)


class ProjectManager(JiraManager):
    def sync(self, remove_old=False):
        from atlassian.models import Project, Issue
        if remove_old:
            Project.objects.all().delete()

        # Do a request to get the projects
        uri = self.get_uri('rest/api/2/project')
        r = requests.get (uri, auth=(self.user, self.token))
        jr = json.loads(r.content)
        # Create the project if it does not exist
        for p_jr in jr:
            # Get the first issue for that project, when it was created
            try:
                issue = Issue.objects.filter(project=p_jr['key']).order_by('created')[0]
            except IndexError:
                continue
            # If not issue is created yet, just don't add the project
            p, created  = Project.objects.get_or_create(key=p_jr['key'], name=p_jr['name'], created_date = issue.created)
            p.save()


class ComponentManager(JiraManager):
    def sync(self, remove_old=False):
        from atlassian.models import Project, Component
        if remove_old:
            Component.objects.all().delete()

        uri_tmpl = 'rest/api/3/project/%s/components'
        # Get every project
        for p in Project.objects.all():
            # Do a request for each project to get the components
            uri = self.get_uri(uri_tmpl % p.key)
            r = requests.get (uri, auth=(self.user, self.token))
            jr = json.loads(r.content)
            # Create the components if it does not exist
            for c_jr in jr:
                c, created  = Component.objects.get_or_create(project=p, name=c_jr['name'])
                c.save()

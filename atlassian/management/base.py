# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class RestJiraCommand(BaseCommand):
    endpoint = ''

    def __init__(self, *args, **kwargs):
        db = settings.DATABASES.get('jira')
        if not db:
            raise CommandError('Missing database named jira')

        self.user = db['USER']
        self.token = db['PASSWORD']
        self.base_uri = db['NAME']
        super(RestJiraCommand, self).__init__(args, kwargs)

    def get_uri(self, endpoint):
        return '%s/%s' % (self.base_uri, endpoint)


class RestConfluenceCommand(BaseCommand):
    endpoint = ''

    def __init__(self, *args, **kwargs):
        db = settings.DATABASES.get('confluence')
        if not db:
            raise CommandError('Missing database named confluence')

        self.user = db['USER']
        self.token = db['PASSWORD']
        self.base_uri = db['NAME']
        super(RestConfluenceCommand, self).__init__(args, kwargs)

    def get_uri(self, endpoint):
        return '%s/%s' % (self.base_uri, endpoint)

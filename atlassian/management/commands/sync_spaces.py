# -*- coding: utf-8 -*-

from datetime import datetime, date
from optparse import make_option
import requests
import json

from atlassian.models import Space
from atlassian.management.base import RestConfluenceCommand

class Command(RestConfluenceCommand):
    help = 'Fill Space model'

    def add_arguments(self, parser):
        parser.add_argument('--remove-old', action='store_true', dest='remove-old',
            default=False,
            help=u"Remove previous spaces found")

    def handle(self, *args, **options):
        # Remove the old projects
        remove_old = options['remove-old']
        if remove_old:
            Space.objects.all().delete()

        uri = self.get_uri('wiki/rest/api/space')
        uri = uri + '?start=%(start)s&limit=25'
        start = 0

        while True:
            current_uri = uri % { 'start': start }
            r = requests.get (current_uri, auth=(self.user, self.token))
            jr = json.loads(r.content)
            for p_jr in jr['results']:
                p, created  = Space.objects.get_or_create(key=p_jr['key'], name=p_jr['name'])
                p.save()
            if jr['size'] < 25:
                break
            else:
                start += 25


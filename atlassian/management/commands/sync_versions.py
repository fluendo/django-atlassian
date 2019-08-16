# -*- coding: utf-8 -*-

from datetime import datetime, date
from optparse import make_option
from datetime import datetime
import requests
import json

from atlassian.models import Project, Version
from atlassian.management.base import RestJiraCommand

class Command(RestJiraCommand):
    help = 'Fill Version model based on the Project model'

    def add_arguments(self, parser):
        parser.add_argument('--remove-old', action='store_true', dest='remove-old',
            default=False,
            help=u"Remove previous versions found")

    def handle(self, *args, **options):
        # Remove the old versions
        remove_old = options['remove-old']
        if remove_old:
            Version.objects.all().delete()

        for p in Project.objects.all():
            uri = self.get_uri('rest/api/2/project/%s/versions' % p.key)
            r = requests.get (uri, auth=(self.user, self.token))
            jr = json.loads(r.content)
            for v_jr in jr:
                v = Version()
                v.name = v_jr['name']
                v.project = p
                v.released = v_jr['released']
                if v.released and v_jr.get('releaseDate'):
                    v.release_date = datetime.strptime(v_jr['releaseDate'], '%Y-%m-%d').date()
                v.save()
            

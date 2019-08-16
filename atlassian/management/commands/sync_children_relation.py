# -*- coding: utf-8 -*-

from optparse import make_option

from atlassian.models import Issue
from django.core.management.base import BaseCommand
from atlassian.management.base import RestJiraCommand

class Command(BaseCommand):
    help = 'Synchronize issue children to be an issue link'

    def add_arguments(self, parser):
        # For specific issue
        parser.add_argument('--issue', action='store', dest='issue',
            help=u"Only for the specified issue")
        # For specific issue type
        parser.add_argument('--issue-type', action='append', dest='issue_type',
            help=u"Only for the specified issue type")
        # For specific project
        parser.add_argument('--project', action='append', dest='project',
            help=u"Only for the specified project")
        # The relation to use
        parser.add_argument('--relation', action='store', dest='relation',
            help=u"The specific relation to use", required=True)

    def handle(self, *args, **options):
        qs = Issue.objects.all()
        if options['issue']:
            qs = qs.filter(key=options['issue'])
        if options['issue_type']:
            qs = qs.filter(issue_type__in=options['issue_type'])
        if options['project']:
            qs = qs.filter(project__in=options['project'])
        for issue in qs:
            relation = getattr(issue.links, options['relation'])
            for children in issue.get_children():
                relation.append(children)

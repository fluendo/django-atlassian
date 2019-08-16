# -*- coding: utf-8 -*-

from optparse import make_option

from atlassian.models import Project
from django.core.management.base import BaseCommand
from atlassian.management.base import RestJiraCommand

class Command(BaseCommand):
    help = 'Fill Project model'

    def add_arguments(self, parser):
        parser.add_argument('--remove-old', action='store_true', dest='remove-old',
            default=False,
            help=u"Remove previous projects found")

    def handle(self, *args, **options):
        # Remove the old projects
        remove_old = options['remove-old']
        Project.objects.sync(remove_old=remove_old)

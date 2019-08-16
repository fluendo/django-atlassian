# -*- coding: utf-8 -*-

from optparse import make_option

from atlassian.models import Component
from django.core.management.base import BaseCommand
from atlassian.management.base import RestJiraCommand

class Command(BaseCommand):
    help = 'Fill Component model'

    def add_arguments(self, parser):
        parser.add_argument('--remove-old', action='store_true', dest='remove-old',
            default=False,
            help=u"Remove previous components found")

    def handle(self, *args, **options):
        # Remove the old components
        remove_old = options['remove-old']
        Component.objects.sync(remove_old=remove_old)


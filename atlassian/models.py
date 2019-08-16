# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json
from datetime import datetime, timedelta

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db import models
from django_atlassian.models.djira import Issue as JiraIssue
from django_atlassian.models.confluence import Content as ConfluenceContent

from atlassian.managers import ProjectManager, ComponentManager

class Issue(JiraIssue):
    def is_parent(self):
        try:
            if len(self.links.contains):
                return True
        except:
            pass
        return super(Issue, self).is_parent()

    def has_parent(self):
        try:
            if len(self.links.is_contained_in):
                return True
        except:
            pass
        return super(Issue, self).has_parent()

    def get_parent(self):
        try:
            return self.links.is_contained_in[0]
        except:
            pass
        return super(Issue, self).get_parent()

    def get_children(self):
        try:
            return self.links.contains
        except:
            pass
        return super(Issue, self).get_children()

    def get_accumulated_progress_time(self):
        changelog = self.get_changelog()
        statuses = self.get_statuses()
        initial_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'To Do']
        progress_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'In Progress']
        terminal_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'Done']
        amount = timedelta(0)
        from_time = None
        for ch in changelog['values']:
            for item in ch['items']:
                if item['field'] == 'status':
                    created = parse_datetime(ch['created'])
                    if from_time:
                        # TODO Remove the weekends to not count into the total amount
                        amount = amount + (created - from_time)
                    if item['toString'] in progress_statuses:
                        from_time = created
                    else: 
                        from_time = None
        if from_time:
            amount = amount + (timezone.now() - from_time)

        return amount

    def transitions(self):
        """
        Return the posible transitions of the issue
        :return dict: Dict of Transitions
        """
        trans = dict(
            [
                (t['name'], t['id']) \
                for t in Issue.jira.transitions(self.key)
            ]
        )
        return trans

    def transition_to(self, transition):
        """
        Set the new transition str
        :param transition str: it is the string of the transition
        """
        trans = self.transitions()
        if transition in trans.keys():
            new_trans = trans[transition]
            return Issue.jira.transition_issue(self, new_trans)
        return None

    def __unicode__(self):
        return str(self.key)


class Project(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    created_date = models.DateField()

    objects = ProjectManager()

    def get_issue_types(self):
        uri = Project.objects.get_uri('rest/api/2/issue/createmeta')
        r = requests.get (uri, auth=(Project.objects.user, Project.objects.token))
        jr = json.loads(r.content)
        # Create the project if it does not exist
        for p_jr in jr['projects']:
            if p_jr['key'] != self.key:
                continue
            return [k['name'] for k in p_jr['issuetypes']]
        return []

    def __unicode__(self):
        return self.key


class Component(models.Model):
    project = models.ForeignKey(Project, blank=False, null=False)
    name = models.CharField(max_length=255)

    objects = ComponentManager()

    def __unicode__(self):
        return self.name


class Label(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Version(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, blank=False, null=False)
    released = models.BooleanField(default=False)
    release_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.name


class Content(ConfluenceContent):
    def __unicode__(self):
        return self.title


class Space(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.key

# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import connections
from django_atlassian.models.djira import Issue
from django_atlassian.models.confluence import Content

class Router(object):

    def __init__(self):
        self.db_jira_alias = None
        self.db_confluence_alias = None
        for alias, settings_dict in settings.DATABASES.items():
            if settings_dict['ENGINE'] == 'django_atlassian.backends.jira':
                self.db_jira_alias = alias
            if settings_dict['ENGINE'] == 'django_atlassian.backends.confluence':
                self.db_confluence_alias = alias

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if self.db_confluence_alias == db:
            return False
        if self.db_jira_alias == db:
            return False
        return None

    def db_for_read(self, model, **hints):
        if issubclass(model, Issue):
            # Check if the model has the AtlassianMeta class
            atlassian_meta = getattr(model, 'AtlassianMeta', False)
            if not atlassian_meta:
                return self.db_jira_alias
            atlassian_db = getattr(atlassian_meta, 'db', False)
            if not atlassian_db:
                return self.db_jira_alias
            for alias, settings_dict in connections.databases.items():
                if settings_dict['ENGINE'] == 'django_atlassian.backends.jira' and \
                    alias == atlassian_db:
                    return alias
            return None

        if issubclass(model, Content):
            return self.db_confluence_alias
        return None

    def db_for_write(self, model, **hints):
        if issubclass(model, Issue):
            # Check if the model has the AtlassianMeta class
            atlassian_meta = getattr(model, 'AtlassianMeta', False)
            if not atlassian_meta:
                return self.db_jira_alias
            atlassian_db = getattr(atlassian_meta, 'db', False)
            if not atlassian_db:
                return self.db_jira_alias
            for alias, settings_dict in connections.databases.items():
                if settings_dict['ENGINE'] == 'django_atlassian.backends.jira' and \
                    alias == atlassian_db:
                    return alias

        if issubclass(model, Content):
            return self.db_confluence_alias

        return None

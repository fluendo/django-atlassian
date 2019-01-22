# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import requests

from django.utils.dateparse import parse_datetime
from django.db.backends.base.introspection import BaseDatabaseIntrospection, TableInfo, FieldInfo

from django_atlassian.backends.common.base import AtlassianDatabaseWrapper, AtlassianDatabaseCursor, AtlassianDatabaseOperations, AtlassianDatabaseConvertion

logger = logging.getLogger('django_atlassian.backends.jira')

class DatabaseIntrospection(BaseDatabaseIntrospection):
    data_types_reverse = {
        'datetime': 'DateField',
        'number': 'FloatField',
        'string': 'TextField',
        'array': 'django_atlassian.models.fields.ArrayField',
        'issuetype': 'TextField',
        'user': 'TextField',
        'project': 'TextField',
        'com.pyxis.greenhopper.jira:gh-epic-status': 'TextField',
    }

    data_type_relations = [
       'com.pyxis.greenhopper.jira:gh-epic-link',
       'com.atlassian.jpo:jpo-custom-field-parent',
       # Fake custom type to handle the hidden parent field
       'com.django-atlassian:parent'
    ]

    columns_read_only = [
        'Σ Time Spent', #'aggregatetimespent',
        'Σ Remaining Estimate', # 'aggregatetimeestimate',
        'Σ Original Estimate', #'aggregatetimeoriginalestimate',
        'Σ Progress', #'aggregateprogress',
        'Attachment', #'attachment',
        'Creator', #'creator',
        'Comment', #'comment',
        'Created', #'created',
        'Description', #'description',
        'Due date', #'duedate',
        'Linked Issues', #issuelinks',
        'Last Viewed', #'lastViewed',
        'Progress', #'progress',
        'Reporter', #'reporter',
        'Resolution', #'resolution',
        'Resolved', #resolutiondate',
        'Security Level', #'security',
        'Sub-tasks', #subtasks',
        'Status', #'status',
        'Remaining Estimate', #'timeestimate',
        'Original Estimate', #'timeoriginalestimate',
        'Time Spent', #timespent',
        'Time Tracking', #timetracking',
        'Updated', #updated',
        'Affects Version/s', #'versions',
        'Watchers', #'watches,',
        'Log Work', #worklog',
        'Work Ratio', #workratio',
        # Custom ones
        '[CHART] Date of First Response',
        '[CHART] Time in Status',
        'Flagged',
        'Epic/Theme',
        'Story Points',
        'Business Value',
        'Sprint',
        'Epic Link',
        'Epic Name',
        'Epic Status',
        'Epic Color',
        'Rank',
        'Organizations',
        'Parent Link', # Conditional with Portfolio
        'Change start date',
        'Change completion date',
        'Request participants',
        'Satisfaction date',
        'Approvers',
        'Story point estimate',
        'Votes',
        'Issue color',
        # Cannot find the parent fied type when saving
        # Error returned is '"parent":"data was not an object",'
        'Parent',
    ]

    def get_table_list(self, cursor):
        return [TableInfo('issue','t')]

    def get_table_description(self, cursor, table_name):
        return cursor.get_fields()

    def get_relations(self, cursor, table_name):
        relations = {}
        content = cursor.get_raw_fields()
        for f in content:
            if f.has_key('schema'):
                if f['schema']['type'] == 'any' and \
                        f['schema']['custom'] in self.data_type_relations:
                    relations[f['clauseNames'][0]] = ('issues', 'issue')
        return relations

    def get_constraints(self, cursor, table_name):
        constraints = {}
        constraints['__primary__'] = {
            'columns': ['key'],
            'primary_key': True,
            'unique': True,
            'foreign_key': False,
            'check': False,
            'index': False
        }
        return constraints


class DatabaseCursor(AtlassianDatabaseCursor):
    arraysize = 100
    uri_search_pattern = '/rest/api/3/search?%(get_opts)s&startAt=%(start_at)s&maxResults=%(max_results)s'
    uri_edit_pattern = '/rest/api/3/issue/%(issue_id)s'
    uri_field = '/rest/api/3/field'

    def get_fields_qs(self, fields):
        return 'fields=%s' % ','.join(f[9] for f in fields)

    def get_sql_qs(self, sql):
        return sql

    def update(self, rows, fields):
        self.rowcount = 0
        body = {
            'fields': {},
            'notifyUsers': False,
        }
        # sanitize the fields
        for f in self.fields:
            if not f[11]:
                continue
            for rf_key, rf_value in fields.iteritems():
                if f[0] == rf_key:
                    body['fields'].update({f[9]: self.db.convertion.to_native(rf_value, f)})
        # update every result
        # TODO Bulk change
        for row in rows:
            uri = self.uri_edit_pattern % {
                'issue_id': row[0]
            }
            response = self.connection.put_request(uri, body)
            if response.status_code not in [requests.codes.ok, 204]:
                logger.warning('JIRA Cloud returned %d for %s', response.status_code, uri)
                continue
            self.rowcount = self.rowcount + 1

    def request(self, get_opts, max_results):
        uri = self.uri_search_pattern % {
            'get_opts': get_opts,
            'start_at': self.opts['start_at'],
            'max_results': max_results,
        }

        response = self.connection.get_request(uri)
        if response.status_code != requests.codes.ok:
            logger.warning('JIRA Cloud returned %d for %s', response.status_code, uri)
            if self.opts['count_only']:
                return tuple([0])
            else:
                return list()

        content = json.loads(response.content)
        issues = content['issues']
        num_issues = len(issues)
        if not num_issues:
            if self.opts['count_only']:
                return tuple([content['total']])
            else:
                return list()

        self.opts['start_at'] += num_issues
        # In case the number is undefined, set it to the returned value
        if (self.opts['max_results'] < 0):
            self.opts['max_results'] = content['total']
        self.opts['max_results'] -= num_issues
        if self.opts['count_only']:
            return tuple([content['total']])
        else:
            return tuple(self.create_row(r) for r in issues)

    def request_fields(self, fields=None):
        """
        Get the raw description for every field id provided
        """
        # The cursor only works for the 'search' endpoint, just call
        # the 'field' endpoint and return all the field types
        response = self.connection.get_request(self.uri_field)
        if response.status_code != requests.codes.ok:
            logger.warning('JIRA Cloud returned %d for %s', response.status_code, self.uri_field)
            return []
        content = json.loads(response.content)
        # Overwrite some fields
        for c in content:
            if c['name'] == 'Epic Status':
                c['schema']['type'] = 'string'
                c['choices'] = (('To Do', 'To Do'), ('In Progress', 'In Progress'), ('Done', 'Done'))
        # The KEY field is never returned
        c = {
            "id": "key",
            "key": "key",
            "name": "Key",
            "custom": False,
            "orderable": True,
            "navigable": True,
            "searchable": True,
            "clauseNames": [
                "key",
            ],
            "schema": {
                "type": "string",
            }
        }
        content.append(c)
        # The parent field is never returned
        c = {
            "id": "parent",
            "key": "parent",
            "name": "Parent",
            "custom": True,
            "orderable": True,
            "navigable": True,
            "searchable": True,
            "clauseNames": [
                "parent",
            ],
            "schema": {
                "type": "any",
                "custom": "com.django-atlassian:parent"
            }
        }
        content.append(c)
        return content

    def create_row(self, row):
        ret = []
        for f in self.fields:
            obj = self.db.convertion.extract(row, f, None)
            if obj:
                ret.append(self.db.convertion.from_native(obj, f))
            else:
                ret.append(obj)
        return ret


class DatabaseConvertion(AtlassianDatabaseConvertion):
    def extract(self, data, field, raw_field):
        if data.has_key(field[9]):
            return data[field[9]]
        elif data['fields'].has_key(field[9]):
            return data['fields'][field[9]]
        else:
            logger.error("Field with id %s and name %s not found", field[8], field[9])
            if field[10] == 'array':
                return []
            else:
                return None

    def insert(self, data, field, raw_field):
        return {field[9]: None}

    def from_native(self, data, field):
        if field[1] == 'project' and data is not None:
            return data['key']
        # Handle the parent
        elif field[1] == 'com.django-atlassian:parent':
            if data:
                return data['key']
            else:
                return None
        # Handle the parent link
        elif field[1] == 'com.atlassian.jpo:jpo-custom-field-parent':
            if data.has_key('data'):
                return data['data']['key']
            else:
                return None
        elif field[1] == 'array' and data is not None:
            if field[10] == 'component':
                return [item['name'] for item in data]
            elif field[10] == 'string':
                return data
            elif field[10] == 'issuelinks':
                return [item['key'] for item in data]
            # Handle Jira Software special array
            elif field[10] == 'com.pyxis.greenhopper.jira:gh-sprint':
                # TODO parse the string properly in the form:
                # u'com.atlassian.greenhopper.service.sprint.Sprint@404966[id=10,rapidViewId=1,state=CLOSED,name=Sprint 6,goal=<null>,startDate=2015-05-20T12:29:00.000Z,endDate=2015-06-02T12:29:00.000Z,completeDate=2015-07-17T12:34:35.717Z,sequence=10]'
                return []
            else:
                return data
        return super(DatabaseConvertion, self).from_native(data, field)


    def to_native(self, data, field):
        if field[1] == 'project' and data is not None:
            return {'key': data}
        # Handle the parent
        elif field[1] == 'com.django-atlassian:parent':
            if data:
                return {'key': data}
            else:
                return None
        # Handle the parent link
        elif field[1] == 'com.atlassian.jpo:jpo-custom-field-parent':
            if data:
                return {'data': {'key': data}}
            else:
                return None
        elif field[1] == 'array':
            if not data:
                return []
            else:
                if field[10] == 'component':
                    return [{'name': item} for item in data]
                elif field[10] == 'string':
                    return data
                elif field[10] == 'issuelinks':
                    return [{'key': item} for item in data]
                else:
                    return []
        return super(DatabaseConvertion, self).to_native(data, field)


class DatabaseOperations(AtlassianDatabaseOperations):
    compiler_module = "django_atlassian.backends.jira.compiler"


class DatabaseWrapper(AtlassianDatabaseWrapper):
    vendor = 'jira'
    cursor_class = DatabaseCursor
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations
    convertion_class = DatabaseConvertion

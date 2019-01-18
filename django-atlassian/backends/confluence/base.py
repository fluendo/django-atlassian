# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json
import logging

from django_atlassian.backends.common.base import AtlassianDatabaseWrapper, AtlassianDatabaseCursor, AtlassianDatabaseOperations, AtlassianDatabaseConvertion

logger = logging.getLogger('django_atlassian.backends.confluence')

class DatabaseCursor(AtlassianDatabaseCursor):
    arraysize = 25

    def get_fields_qs(self, fields):
        new_fields = ','.join(f[9] for f in fields if f[9] is not None)
        if new_fields:
            return 'expand=%s' % new_fields

    def get_sql_qs(self, sql):
        # For empty queries add a fake 'created' filter,
        # Confluence does not accept empty cql parameter
        query = sql.split('=')
        if not query[1]:
            query[1] = "created >= '1970/01/01'"
        return '='.join(query)


    def request_fields(self, fields=None):
        content = [
            {
                'id': None,
                'clauseNames': ['id',],
                'schema': { 'type': 'string', },
                'returnName': 'id',
            },
            {
                'id': 'history',
                'clauseNames': ['creator',],
                'schema': { 'type': 'string', },
                'returnName': 'history.createdBy.username',
            },
            {
                'id': 'history',
                'clauseNames': ['created',],
                'schema': { 'type': 'datetime', },
                'returnName': 'history.createdDate'
            },
            {
                'id': None,
                'clauseNames': ['type',],
                'schema': { 'type': 'string', },
                'returnName': 'type',
            },
            {
                'id': None,
                'clauseNames': ['title',],
                'schema': { 'type': 'string', },
                'returnName': 'title',
            },
            {
                'id': 'space',
                'clauseNames': ['space',],
                'schema': { 'type': 'string', },
                'returnName': 'space.key',
            },
        ]
        return content

    def request(self, get_opts, max_results):
        if self.opts['count_only']:
            uri_pattern = '%(uri)s/wiki/rest/api/search?%(get_opts)s&start=%(start_at)s&limit=%(max_results)s'
        else:
            uri_pattern = '%(uri)s/wiki/rest/api/content/search?%(get_opts)s&start=%(start_at)s&limit=%(max_results)s'

        uri = uri_pattern % {
            'uri': self.connection.uri,
            'get_opts': get_opts,
            'start_at': self.opts['start_at'],
            'max_results': max_results,
        }

        logger.error('uri=%s', uri)
        request = requests.get(uri, auth=(self.connection.user, self.connection.password))
        if not request:
          if self.opts['count_only']:
              return tuple([0])
          else:
              return list()

        content = json.loads(request.content)
        issues = content['results']
        num_issues = len(issues)
        if not num_issues:
            if self.opts['count_only']:
                return tuple([content['totalSize']])
            else:
                return list()

        self.opts['start_at'] += num_issues
        if (self.opts['max_results'] > 0):
            self.opts['max_results'] -= num_issues
        if self.opts['count_only']:
            return tuple([content['totalSize']])
        else:
            return tuple(self.create_row(r) for r in issues)

    def create_row(self, row):
        ret = []
        for f,r in zip(self.fields, self.raw_fields):
            obj = self.db.convertion.extract(row, f, r)
            if obj:
                ret.append(self.db.convertion.from_native(obj, f))
            else:
                ret.append(obj)
        return ret


class DatabaseConvertion(AtlassianDatabaseConvertion):
    def extract(self, data, field, raw_field):
        if raw_field.has_key('returnName'):
            return_name = raw_field['returnName']
            value = row
            for rn in return_name.split('.'):
                value = value[rn]
            return value
        elif row.has_key(field[9]):
            return row[field[9]]
        else:
            return None

class DatabaseOperations(AtlassianDatabaseOperations):
    compiler_module = "django_atlassian.backends.confluence.compiler"


class DatabaseWrapper(AtlassianDatabaseWrapper):
    vendor = 'confluence'
    cursor_class = DatabaseCursor
    ops_class = DatabaseOperations
    convertion_class = DatabaseConvertion

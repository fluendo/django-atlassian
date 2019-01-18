# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple
import requests
import re
import logging
import json

from django.utils.dateparse import parse_datetime
from django.contrib.auth import get_user_model

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.base.validation import BaseDatabaseValidation
from django.db.backends.base.introspection import BaseDatabaseIntrospection, FieldInfo

# Extend the FieldInfo to also have:
# field_name: The model field name
# field_id: The field id
# array_type: In case of being an array, the element's type
FieldInfo = namedtuple('FieldInfo', FieldInfo._fields + ('field_name', 'field_id', 'array_type', 'editable', 'options'))
logger = logging.getLogger('django_atlassian.backends.common')

class AtlassianDatabaseIntrospection(BaseDatabaseIntrospection):
    pass


class AtlassianDatabaseConnection(object):
    def __init__(self, uri, user, password, sc):
        self.uri = uri
        self.user = user
        self.password = password
        self.sc = sc

    def rollback(self):
        return True

    def commit(self):
        return True

    def get_request(self, part):
        uri = self.uri + part
        headers = {'Accept': 'application/json'}
        if self.user and self.password:
            r = requests.get(uri, auth=(self.user, self.password), headers=headers)
        elif self.sc:
            token = self.sc.create_token('GET', uri)
            headers.update({'Authorization': 'JWT {}'.format(token)})
            r = requests.get(uri, headers=headers)
        else:
            return None
        return r

    def put_request(self, part, body):
        json_body = json.dumps(body)
        uri = self.uri + part
        headers = {'Content-Type': 'application/json'}
        if self.user and self.password:
            r = requests.put(uri, data=json_body, auth=(self.user, self.password), headers=headers)
        elif self.sc:
            token = self.sc.create_token('PUT', uri)
            headers.update({'Authorization': 'JWT {}'.format(token)})
            r = requests.put(uri, data=json_body, headers=headers)
        else:
            return None
        return r

    def post_request(self, part, body, header=None, fil=None):
        json_body = json.dumps(body)
        uri = self.uri + part
        headers = {'Content-Type': 'application/json'}
        if header and isinstance(header, dict) and fil:
            headers = header
        if self.user and self.password:
            if fil:
                r = requests.post(uri, files=fil, auth=(self.user, self.password), headers=headers)
            else:
                r = requests.post(uri, data=json_body, auth=(self.user, self.password), headers=headers)
        elif self.sc:
            token = self.sc.create_token('POST', uri)
            headers.update({'Authorization': 'JWT {}'.format(token)})
            if fil:
                r = requests.post(uri, files=fil, headers=headers)
            else:
                r = requests.post(uri, data=json_body, headers=headers)
        else:
            return None
        return r

    def delete_request(self, part):
        uri = self.uri + part
        if self.user and self.password:
            r = requests.delete(uri, auth=(self.user, self.password))
        elif self.sc:
            token = self.sc.create_token('DELETE', uri)
            headers.update({'Authorization': 'JWT {}'.format(token)})
            r = requests.delete(uri)
        else:
            return None
        return r

class AtlassianDatabase(object):
    Error = requests.exceptions.RequestException

    class DatabaseError(Error):
        pass

    class OperationalError(DatabaseError):
        pass

    class IntegrityError(DatabaseError):
        pass

    class DataError(DatabaseError):
        pass

    class InterfaceError(DatabaseError):
        pass

    class InternalError(DatabaseError):
        pass

    class ProgrammingError(DatabaseError):
        pass

    class NotSupportedError(DatabaseError):
        pass


class AtlassianDatabaseValidation(BaseDatabaseValidation):
    pass


class AtlassianDatabaseOperations(BaseDatabaseOperations):
    def quote_name(self, name):
        return name

    def no_limit_value(self):
        return None


class AtlassianDatabaseFeatures(BaseDatabaseFeatures):
    can_use_chunked_reads = False
    supports_transactions = False
    supports_select_union = False
    supports_select_intersection = False
    supports_select_difference = False
    
    def __init__(self, connection):
        self.connection = connection


class AtlassianDatabaseCreation(BaseDatabaseCreation):
    def create_test_db(self, *args, **kwargs):
        """
        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        pass

    def destroy_test_db(self, *args, **kwargs):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        pass


class AtlassianDatabaseConvertion(object):
    def __init__(self, connection):
        self.connection = connection

    def extract(self, data, field, raw_field):
        raise NotImplementedError('missing extract implementation')

    def insert(self, data, field, raw_field):
        raise NotImplementedError('missing insert implementation')

    def from_native(self, data, field):
        if field[1] == 'datetime' and data is not None:
            return parse_datetime(data)
        elif field[1] == 'number' and data is not None:
            return float(data)
        elif field[1] in ['user', 'issuetype'] and data is not None:
            return data['name']
        else:
            if field[12] and data.has_key('value'):
                return data['value']
            return data

    def to_native(self, data, field):
        if field[1] == 'datetime' and data is not None:
            return None
        elif field[1] == 'number' and data is not None:
            return float(data)
        elif field[1] in ['user', 'issuetype'] and data is not None:
            return {'name': data}
        else:
            if field[12]:
                return {'value': data}
            return data
        pass


class AtlassianDatabaseCursor(object):
    def __init__(self, connection, db):
        self.connection = connection
        self.db = db
        self.sql = None
        self.fields = None
        self.raw_fields = None
        self.rowcount = 0

    def __normalize_field_name(self, name):
        normal = re.sub(r'\W', '_', name).lower()
        normal = re.sub(r'_{2,}', '_', normal)
        if normal[0] == '_':
            normal = normal[1:] 
        return normal

    def close(self):
        self.connection = None
        self.sql = None
        self.fields = None
        self.raw_fields = None

    def execute(self, sql, params=None):
        #print "EXECUTE %s" % sql
        #print params
        #print "DONE EXECUTE"

        opts = {}
        new_params = []
        # split the params into options and real params
        if params:
            for i in params:
                if type(i) == dict:
                    opts.update (i)
                else:
                    new_params.extend([i])

        if not opts.has_key ('start_at'):
            opts['start_at'] = 0
        if not opts.has_key ('max_results'):
            opts['max_results'] = -1
        if not opts.has_key ('count_only'):
            opts['count_only'] = False
        self.opts = opts
        self.sql = self.get_sql_qs(sql)
        self.sql = self.sql % tuple(self.escape_type(p) for p in new_params)

        # Only include the requested fields
        if opts.has_key('fields'):
            # The fields have the name of the 'clause' used, but we need to use
            # the 'id' to tell the API what fields to expand
            fields_s = opts['fields']
            fields = fields_s.split(',')
            # keep track of the raw fields
            self.raw_fields = self.get_raw_fields(fields)
            # replace the fields with the corresponding 'id'
            self.fields = self.get_fields(fields)
        # Check if we need to update
        if opts.has_key('update_fields'):
            rows = self.fetchmany()
            self.update(rows, opts['update_fields'])

    def fetchone(self):
        return self.fetchmany ()

    def fetchmany(self, size=None):
        max_results = self.opts['max_results']
        if size is None:
            size = self.arraysize

        if max_results < 0:
            max_results = self.arraysize
        elif max_results == 0:
            return list()
        elif max_results > self.arraysize:
            max_results = self.arraysize

        if self.opts['count_only']:
            max_results = 1

        if size < max_results:
            max_results = size

        get_opts = ''
        if self.fields and self.get_fields_qs:
            fields_qs = self.get_fields_qs(self.fields)
            if fields_qs:
                get_opts += fields_qs
                get_opts += '&'
        get_opts += self.sql
        return self.request(get_opts, max_results)

    def get_raw_fields(self, fields=None):
        content = self.request_fields(fields)
        ret = []

        if fields:
            for f in fields:
                for c in content:
                    if c.has_key('schema'):
                        if c.has_key('clauseNames') and c['clauseNames'] and c['clauseNames'][0] == f:
                            ret.append(c)
        else:
            ret = content
        return ret
 
    def get_fields(self, fields=None):
        """ 
        Method to return the FieldInfo and the field API id's
        If use_id = False, then the returned field names are the ones
        used for the query clause. If it is True, the field names
        used on the expand/select are used. The fields parameter is
        used to filter the result
        """ 
        ret = []
        if not self.raw_fields:
            self.raw_fields = self.get_raw_fields(fields)
        for f in self.raw_fields:
            if f.has_key('schema') and f.has_key('clauseNames') and f['clauseNames']:
                schema = f['schema']['type']
                array_type = None
                if schema == 'any' and f['schema']['custom']:
                    schema = f['schema']['custom']
                if schema == 'array':
                    array_type = f['schema'].get('custom', f['schema']['items'])
                editable = True
                if hasattr(self.db.introspection, 'columns_read_only'):
                    editable = f['name'] not in self.db.introspection.columns_read_only
                choices = f.get('choices', None)
 
                ret.append(FieldInfo(f['clauseNames'][0], schema, None, None, None, None, True, None, self.__normalize_field_name(f['name']), f['id'], array_type, editable, choices))
        return ret

    def escape_type(self, value):
        if type(value) == unicode or type(value) == str:
            return "'%s'" % value
        else:
            return value

    def get_sql_qs(self, sql):
        raise NotImplementedError('missing get_sql_qs implementation')

    def request(self, get_opts):
        raise NotImplementedError('missing request implementation')

    def update(self, rows, fields):
        raise NotImplementedError('missing update implementation')


class AtlassianDatabaseWrapper(BaseDatabaseWrapper):
    # Hook for sibling classes
    client_class = BaseDatabaseClient
    creation_class = AtlassianDatabaseCreation
    features_class = AtlassianDatabaseFeatures
    validation_class = AtlassianDatabaseValidation
    connection_class = AtlassianDatabaseConnection
    introspection_class = AtlassianDatabaseIntrospection
    convertion_class = AtlassianDatabaseConvertion
    charset = 'utf-8'

    Database = AtlassianDatabase

    pattern_esc = r"REPLACE(REPLACE(REPLACE({}, '\', '\\'), '%%', '\%%'), '_', '\_')"
    pattern_ops = {
        'contains': r"LIKE '%%' || {} || '%%' ESCAPE '\'",
        'icontains': r"LIKE '%%' || UPPER({}) || '%%' ESCAPE '\'",
        'startswith': r"LIKE {} || '%%' ESCAPE '\'",
        'istartswith': r"LIKE UPPER({}) || '%%' ESCAPE '\'",
        'endswith': r"LIKE '%%' || {} ESCAPE '\'",
        'iendswith': r"LIKE '%%' || UPPER({}) ESCAPE '\'",
    }
    operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE BINARY %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE BINARY %s',
        'endswith': 'LIKE BINARY %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }

    def __init__(self, *args, **kwargs):
        super(AtlassianDatabaseWrapper, self).__init__(*args, **kwargs)
        self.autocommit = True
        self.convertion = self.convertion_class(self)

    def get_connection_params(self):
        """Compute appropriate parameters for establishing a new connection."""
        if not self.connection_class:
            raise NotImplementedError('missing connection class attribute')
        
        return self.connection_class(self.settings_dict['NAME'],
                self.settings_dict['USER'], self.settings_dict['PASSWORD'],
                self.settings_dict['SECURITY'])

    def get_new_connection(self, conn_params):
        return conn_params

    def create_cursor(self, name=None):
        if not self.cursor_class:
            raise NotImplementedError('missing cursor class attribute')
        return self.cursor_class (self.connection, self)

    def close(self):
        self.connection = None

    def init_connection_state(self):
        pass

    def _set_autocommit(self, autocommit):
        pass


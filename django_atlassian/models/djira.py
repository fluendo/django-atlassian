# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import importlib
import json
import requests
import re
import collections
import os
import copy

from django.db import models, router, connections
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import class_prepared
from django.db.models.manager import Manager, EmptyManager

from django_atlassian.models.connect import SecurityContext
from django_atlassian.backends.jira.base import DatabaseConvertion
from django_atlassian.models.fields import ArrayField

from jira import JIRA
from jira.resources import Issue as JiraIssue
from jira.resilientsession import ResilientSession

logger = logging.getLogger('django_atlassian')

class IssueManager(Manager):

    def create_from_json(self, json):
        """
        Some modules notify with an Issue. In order to manage it in a django way
        we need to convert the json received into a real Issue instance object
        relative to the database the manager belongs to
        """
        convert = DatabaseConvertion(None)
        args = {}
        for x in self.model.AtlassianMeta.description:
            field = self.model._meta.get_field(x[8])
            value = convert.extract(json, x, None)
            if value:
                value = convert.from_native(value, x)
            if type(field) == models.ForeignKey and value:
                args[x[8]] = self.get(key=value)
            else:
                args[x[8]] = value
        return self.model(**args)


class JiraManagerMixin(JIRA):
    def __init__(self, *args, **kwargs):
        try:
            db_alias = router.db_for_read(self.model)
            db_settings = connections.databases[db_alias]
            if db_settings['USER'] and db_settings['PASSWORD']:
                super(JiraManagerMixin, self).__init__(
                        server=db_settings['NAME'],
                        basic_auth=(
                            db_settings['USER'],
                            db_settings['PASSWORD']
                        )
                )
            elif db_settings['SECURITY']:
                jwt = {
                    'secret': db_settings['SECURITY'].shared_secret,
                    'payload': {'iss': db_settings['SECURITY'].key},
                }
                super(JiraManagerMixin, self).__init__(
                    server=db_settings['NAME'],
                    jwt=jwt
                )
        except Exception as err:
            logger.error(err)


class JiraManager(EmptyManager, JiraManagerMixin):

    def __init__(self, *args, **kwargs):
        super(JiraManager, self).__init__(None)

    def __setattr__(self, attrname, val):
        if attrname == 'model':
            if val:
                super(JiraManager, self).__init__(None)
        super(JiraManager, self).__setattr__(attrname, val)


class IssueLinkList(collections.MutableSequence):
    """
    IssueLink abstraction
    """
    uri_get = '/rest/api/3/issue/%(key)s?fields=issuelinks'
    uri_create = '/rest/api/3/issueLink'
    uri_delete = '/rest/api/3/issueLink/%(link_id)s'

    def __init__(self, model, db, link_type, inward):
        self.model = model
        self.db = db
        self.link_type = link_type
        self.inward = inward

    def __len__(self):
        uri = self.uri_get % {
            'key': self.model.key,
        }
        response = self.db.connection.get_request(uri)
        response.raise_for_status()
        content = json.loads(response.content)
        count = 0
        for x in content['fields']['issuelinks']:
            if x['type']['id'] == self.link_type['id']:
                if self.inward and x.has_key('inwardIssue'):
                    count = count + 1
                elif not self.inward and x.has_key('outwardIssue'):
                    count = count + 1
        return count

    def __delitem__(self, index):
        link_id, link = self.__getlink__(index)
        uri = self.uri_delete % {
            'link_id': link_id
        }
        response = self.db.connection.delete_request(uri)
        response.raise_for_status()

    def __setitem__(self, index, value):
        raise NotImplementedError

    def insert(self, index, value):
        if not isinstance(value, self.model._meta.model):
            raise TypeError('The value must be an Issue')

        if index != len(self):
            raise IndexError
        body = {
            'type': { 'name': self.link_type['name'] },
        }
        if self.inward:
            body['inwardIssue'] = {'key': value.key}
            body['outwardIssue'] = {'key': self.model.key}
        else:
            body['inwardIssue'] = {'key': self.model.key}
            body['outwardIssue'] = {'key': value.key}

        response = self.db.connection.post_request(self.uri_create, body)
        response.raise_for_status()

    def __getitem__(self, index):
        link_id, link = self.__getlink__(index)
        key = link['key']
        return self.model._meta.model.objects.get(key=key)

    def __getlink__(self, index):
        uri = self.uri_get % {
            'key': self.model.key,
        }
        response = self.db.connection.get_request(uri)
        response.raise_for_status()

        content = json.loads(response.content)
        count = 0
        link = None
        link_id = 0
        for x in content['fields']['issuelinks']:
            if x['type']['id'] == self.link_type['id']:
                if self.inward and x.has_key('inwardIssue'):
                    if count == index:
                        link = x['inwardIssue']
                        link_id = x['id']
                        break
                    count = count + 1
                elif not self.inward and x.has_key('outwardIssue'):
                    if count == index:
                        link = x['outwardIssue']
                        link_id = x['id']
                        break
                    count = count + 1
        if not link:
            raise IndexError("list index out of range")
        return link_id, link


class IssueLinks(object):
    """
    IssueLinks abstraction
    """

    db = None
    key = None
    uri_get_all = '/rest/api/3/issueLinkType'
    uri_get = '/rest/api/3/issue/%(key)s?fields=issuelinks'

    def __init__(self, model):
        db_alias = router.db_for_read(model._meta.model)
        db_settings = connections.databases[db_alias]
        if db_settings['ENGINE'] != 'django_atlassian.backends.jira':
            return

        self.db = connections[db_alias]
        self.model = model

    def __normalize(self, name):
        normal = re.sub(r'\W', '_', name).lower()
        normal = re.sub(r'_{2,}', '_', normal)
        return normal

    def __getattr__(self, name):
        # Get every link type
        response = self.db.connection.get_request(self.uri_get_all)
        if response.status_code != requests.codes.ok:
            raise AttributeError("'IssueLinks' has no attribute %s" % name)
        
        content = json.loads(response.content)
        link_type = None
        inward = False
        for x in content['issueLinkTypes']:
            if name == self.__normalize(x['inward']):
                inward = True
                link_type = x
                break
            elif name == self.__normalize(x['outward']):
                inward = False
                link_type = x
                break

        if not link_type:
            raise AttributeError("'IssueLinks' has no attribute %s" % name)

        return IssueLinkList(self.model, self.db, link_type, inward)


class Attachment(object):
    """
    Attachment class for jira issue
    """
    def __init__(self, obj, db):
        self.db = db
        for key, value in obj.iteritems():
            if isinstance(value, dict):
               self.__init__(value, db)
            else:
                setattr(self, key, value)

    def __getattr__(self, attr):
        return "'Attachment' attribute {} not defined".format(attr)

    def delete(self):
        uri = '/rest/api/3/attachment/{}'.format(self.id)
        try:
            response = self.db.connection.delete_request(uri)
            return response.status_code
        except Exception as e:
            raise e

class JiraIssueModel(JiraIssue):
    def __init__(self, *args, **kwargs):
        options = copy.copy(JIRA.DEFAULT_OPTIONS)
        session = ResilientSession()
        jwt = None
        if self.AtlassianMeta.db:
            # dynamic models via jira-addon
            db = connections.databases[self.AtlassianMeta.db]
            options['server'] = db['NAME']
            sc = db['SECURITY']
            jwt = {
                'secret': sc.shared_secret,
                'payload': {'iss': sc.key},
            }
        else:
            # static models 
            db = self.get_db().connection
            options['server'] = db.uri
            session.auth = (db.user, db.password)

        # Jira model init self.key = None, keep a copy & restore
        self.jira_key = self.key
        super(JiraIssueModel, self).__init__(options, session)
        self.key = self.jira_key
        if jwt:
            self._session = self.__class__.jira._session


class Issue(models.base.Model, JiraIssueModel):
    """
    Base class for all JIRA Issue models.
    """

    # The only mandatory field we add here is the KEY. For half-dynamic models
    # it is required to have a primary key otherwise django will create one for
    # us.
    key = models.CharField(max_length=255, primary_key=True, unique=True)
    objects = IssueManager()
    jira = JiraManager()

    def __init__(self, *args, **kwargs):
        super(Issue, self).__init__(*args, **kwargs)
        self.find(self.jira_key)

    def __getattr__(self, name):
        if name == 'links':
            self.links = IssueLinks(self)
            return self.links
        raise AttributeError("'Issue' has no attribute %s" % name)

    def get_db(self):
        db_alias = router.db_for_read(self._meta.model)
        db_settings = connections.databases[db_alias]
        if db_settings['ENGINE'] != 'django_atlassian.backends.jira':
            return None
        return connections[db_alias]

    def get_property(self, prop_name):
        # Create a connection
        # Call curl -X GET https://jira-instance1.net/rest/api/3/issue/ENPR-4/properties/{propertyKey}
        pass

    def set_property(self, prop_name, value):
        # Create a connection
        # Call curl -X PUT -H "Content-type: application/json" https://jira-instance1.net/rest/api/3/issue/`ENPR-4`/properties/{propertyKey} -d '{"content":"Test if works on Jira Cloud", "completed" : 1}'
        pass

    def is_parent(self):
        """
        Return True if the issue is a parent issue, False otherwise
        """
        if self.epic_linked.exists():
            return True
        elif self.sub_tasks:
            return True
        else:
            return False

    def has_parent(self):
        """ 
        Return True if the issue has a parent, False otherwise
        """
        if self.epic_link_id is not None:
            return True
        if self.parent_link_id is not None:
            return True
        if self.parent_id is not None:
            return True
        return False 

    def get_parent(self):
        """ 
        Get the parent issue depending on the issue type
        """
        if self.epic_link_id is not None:
            return self.epic_link
        if self.parent_link_id is not None:
            return self.parent_link
        if self.parent_id is not None:
            return self.parent
        return None

    def get_children(self):
        """
        Get the children issues depending on the isue type
        """
        if self.epic_linked.exists():
            return self.epic_linked.all()
        elif self.sub_tasks:
            return self._meta.model.objects.filter(key__in=self.sub_tasks)
        else:
            return []

    def get_changelog(self):
        """
        Get the Issue's changelog
        """
        uri = "/rest/api/3/issue/%(issue)s/changelog" % { 'issue': self.key }
        response = self.get_db().connection.get_request(uri)
        response.raise_for_status()
        content = json.loads(response.content)
        return content

    def get_statuses(self):
        """
        Get the available statuses on the system
        """
        uri = "/rest/api/3/status"
        response = self.get_db().connection.get_request(uri)
        response.raise_for_status()
        content = json.loads(response.content)
        return content
    
    def get_attachment(self):
        """
        Get an url list of attached files
        """
        response = self.attachment
        content = [  Attachment(file, self.get_db()) for file in response]
        return content

    def add_attachment(self, attachment, filename=None):
        """
        Attach a new file
        :param attachment: a file like object
        :param filename: a file name
        """
        uri = "/rest/api/3/issue/{}/attachments".format(self.key)
        if isinstance(attachment, str):
            attachment = open(attachment, "rb") 

        if not filename:
            filename = os.path.basename(attachment.name)

        try:
            response = self.get_db().connection.post_request(uri, body={}, header={'content-type': None, 'X-Atlassian-Token': 'nocheck'},
                                                  fil={'file': (filename, attachment, 'application/octet-stream')})
            return response
        except Exception as e:
            raise e

    def delete_attachment(self, attachment):
        """
        Delete attachment file
        :param attachment: it is an Attachment object
        """
        uri = '/rest/api/3/attachment/{}'.format(attachment.id)

        try:
            response = self.get_db().connection.delete_request(uri)
            return response.status_code
        except Exception as e:
            raise e 

    def __unicode__(self):
        return str(self.key)

    class Meta:
        abstract = True


class AtlassianMeta:
    """
    Base class for all JIRA related Meta.
    """

    def __init__(self):
        # The database name this model refers to. Even if this breaks django
        # purpose of resuable models being independent of the database backend,
        # for JIRA there's 1:1 relation between the database (connection) and the model
        self.db = None
        # The set of FieldInfo as returned by the introspection
        # get_table_description(). Given that several REST API methods return a
        # full issue in JSON, we can parse it directly without the need of another
        # round trip to the server
        self.description = []


def create_model(name):
    # Create the module dynamically
    class Meta:
        pass
    setattr(Meta, 'app_label', 'django_atlassian')
    setattr(Meta, 'managed', False)

    am = AtlassianMeta()
    am.db = name

    # Set up a dictionary to simulate declarations within a class
    attrs = {
        '__module__': create_model.__module__, 
        'Meta': Meta,
        'AtlassianMeta': am
    }
    logger.info("Creating model %s", name)
    model = type(name, (Issue,), attrs)
    return model


def populate_model(db, model):
    # Double check the model does have an AtlassianMeta
    am = getattr(model, 'AtlassianMeta', None)
    if not am:
        am = AtlassianMeta()
        setattr(model, 'AtlassianMeta', am)
    # Check if the description is already populated
    if am.description:
        return
        
    logger.info("Populating model %s", model)
    # Create a cursor to inspect the database for the fields
    with db.cursor() as cursor:
        try:
            relations = db.introspection.get_relations(cursor, 'issue')
        except NotImplementedError:
            relations = {}
        try:
            constraints = db.introspection.get_constraints(cursor, 'issue')
        except NotImplementedError:
            constraints = {}
        primary_key_column = db.introspection.get_primary_key_column(cursor, 'issue')
        unique_columns = [
            c['columns'][0] for c in constraints.values()
            if c['unique'] and len(c['columns']) == 1
        ]
        table_description = db.introspection.get_table_description(cursor, 'issue')
        for row in table_description:
            extra_params = {}
            column_name = row[0]
            field_name = row[8]
            choices = row[12]
            is_relation = column_name in relations

            # Use the correct column name
            extra_params['db_column'] = column_name
            # Skip the primary key, we already have one
            if column_name == primary_key_column:
                am.description.append(row)
                continue
            # Add unique, if necessary.
            if column_name in unique_columns:
                extra_params['unique'] = True

            # Add choices if needed
            if choices:
                extra_params['choices'] = choices

            if is_relation:
                field_type = 'ForeignKey'
                rel_to = (
                    "self" if relations[column_name][1] == 'issue'
                    else None
                )
            else:
               try:
                   field_type = db.introspection.get_field_type(row[1], row)
               except KeyError:
                   field_type = None

            if field_type:
                field_module = 'django.db.models' if '.' not in field_type else '.'.join(field_type.split('.')[:-1])
                field_class = field_type if '.' not in field_type else field_type.split('.')[-1]
                logger.info("Adding field '%s' for column '%s' for class '%s'", field_name, column_name, field_class) 
                try:
                    field_module = importlib.import_module(field_module)
                    try:
                        field_cls = getattr(field_module, field_class)
                    except AttributeError:
                        logger.error("Class '%s' does not exist", field_class)
                        continue
                except ImportError:
                    logger.error("Module '%s' does not exist", field_module)
                    continue

                if field_type == 'ForeignKey' and rel_to:
                    field = field_cls(rel_to, related_name='%sed' % field_name, **extra_params)
                else:
                    field = field_cls(**extra_params)

                if field:
                    am.description.append(row)
                    field.contribute_to_class(model, field_name)
                else:
                    logger.warning("Field '%s' can not be added", field_name)


def add_fields(sender, **kwargs):
    """
    Will add the corresponding fields for the database this
    model belongs to
    """
    db_alias = router.db_for_read(sender)
    db = connections.databases[db_alias]
    if db['ENGINE'] != 'django_atlassian.backends.jira':
        return

    connection = connections[db_alias]
    logger.info("Class %s prepared, populating", sender)
    populate_model(connection, sender)

 
class_prepared.connect(add_fields)

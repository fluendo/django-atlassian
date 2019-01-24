# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import atlassian_jwt
import threading

from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.db import models, connections
from django.db.utils import ConnectionDoesNotExist 

from django_atlassian.models.connect import SecurityContext
from django_atlassian.models.djira import create_model, populate_model

logger = logging.getLogger('django_atlassian')
lock = threading.Lock()

class DjangoAtlassianAuthenticator(atlassian_jwt.Authenticator):
    def get_shared_secret(self, client_key):
        sc = SecurityContext.objects.filter(client_key=client_key).get()
        return sc.shared_secret


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        headers = {}
        query = ''
        if request.method == 'POST':
            headers['Authorization'] = request.META.get('HTTP_AUTHORIZATION', None)
        # Generate the query
        params = []
        for key in request.GET.iterkeys():
            params.append("%s=%s" % (key, request.GET.get(key, None)))
        query = "&".join(params)

        auth = DjangoAtlassianAuthenticator()
        uri = request.path
        if query:
            uri = "%s?%s" % (uri, query)
        try:
            client_key = auth.authenticate(request.method, uri, headers)
        except Exception as e:
            return None

        sc = SecurityContext.objects.filter(client_key=client_key).get()
        # Setup the request attributes, the security context and the model
        try:
            db = connections[client_key]
        except ConnectionDoesNotExist:
            connections.databases[client_key] = self._create_database(client_key, sc)
            db = connections[client_key]

        with lock: 
            try:
                model = apps.get_model('django_atlassian', client_key)
            except LookupError:
                logger.info("Model %s not found, creating it", str(client_key))
                model = create_model(str(client_key))

        request.atlassian_model = model
        request.atlassian_sc = sc
        request.atlassian_db = db
        return None


    def _create_database(self, name, sc):
        new_db = {}
        new_db['id'] = name
        new_db['ENGINE'] = 'django_atlassian.backends.jira'
        new_db['NAME'] = sc.host
        new_db['USER'] = ''
        new_db['PASSWORD'] = ''
        new_db['HOST'] = ''
        new_db['PORT'] = ''
        new_db['SECURITY'] = sc
        return new_db

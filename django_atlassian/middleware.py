# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import atlassian_jwt
from atlassian_jwt.url_utils import hash_url, parse_query_params

import threading
import jwt
from jwt import DecodeError

from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.db import models, connections
from django.db.utils import ConnectionDoesNotExist 

from django.core.exceptions import PermissionDenied
from django_atlassian.models.connect import SecurityContext
from django_atlassian.models.djira import create_model, populate_model

logger = logging.getLogger('django_atlassian')
lock = threading.Lock()

class DjangoAtlassianAuthenticator(atlassian_jwt.Authenticator):
    def get_shared_secret(self, client_key):
        sc = SecurityContext.objects.filter(client_key=client_key).get()
        return sc.shared_secret

    def claims(self, http_method, url, headers=None, qsh_check_exempt=False):
        token = self._get_token(
            headers=headers,
            query_params=parse_query_params(url))

        claims = jwt.decode(token, verify=False, algorithms=self.algorithms,
                            options={"verify_signature": False})
        if not qsh_check_exempt and claims['qsh'] != hash_url(http_method, url):
            raise DecodeError('qsh does not match')

        # verify shared secret
        jwt.decode(
            token,
            audience=claims.get('aud'),
            key=self.get_shared_secret(claims['iss']),
            algorithms=self.algorithms,
            leeway=self.leeway)

        return claims


class JWTAuthenticationMiddleware(MiddlewareMixin):
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

    def _check_jwt(self, request, qsh_check_exempt=False):
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

        claims = auth.claims(request.method, uri, headers, qsh_check_exempt)
        return claims

    def process_view(self, request, view_func, view_args, view_kwargs):
        jwt_required = getattr(view_func, 'jwt_required', False)
        if not jwt_required:
            return None

        jwt_qsh_exempt = getattr(view_func, 'jwt_qsh_exempt', False)

        try:
            claims = self._check_jwt(request, qsh_check_exempt=jwt_qsh_exempt)
            client_key = claims['iss']
        except Exception as e:
            raise PermissionDenied

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
        request.atlassian_account_id = claims.get('sub')
        return None

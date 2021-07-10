# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import jwt
import time
import json
import urlparse
import urllib
import hashlib
import base64
import atlassian_jwt
from atlassian_jwt.url_utils import hash_url
import requests

from django.db import models

class SecurityContext(models.base.Model):
    """
    Stores the security context shared on the installation
    handshake process
    """

    shared_secret = models.CharField(max_length=512, null=False, blank=False)
    key = models.CharField(max_length=512, null=False, blank=False)
    client_key = models.CharField(max_length=512, null=False, blank=False)
    host = models.CharField(max_length=512, null=False, blank=False)
    product_type = models.CharField(max_length=512, null=False, blank=False)
    oauth_client_id = models.CharField(max_length=512, null=True, blank=True)

    def create_token(self, method, uri, account=None):
        if not account:
            token = atlassian_jwt.encode_token(method, uri, self.client_key, self.shared_secret)
        else:
            now = int(time.time())
            token = jwt.encode(key=self.shared_secret, algorithm='HS256', payload={
                'aud': self.client_key,
                'sub': account,
                'iss': self.client_key,
                'qsh': hash_url(method, uri),
                'iat': now,
                'exp': now + 30,
            })
            if isinstance(token, bytes):
                token = token.decode('utf8')
        return token

    def create_user_token(self, account_id):
        now = int(time.time())
        token = jwt.encode(key=self.shared_secret, algorithm='HS256', payload={
            'iss': 'urn:atlassian:connect:clientid:{}'.format(self.oauth_client_id),
            'sub': 'urn:atlassian:connect:useraccountid:{}'.format(account_id),
            'tnt': self.host,
            'aud': 'https://oauth-2-authorization-server.services.atlassian.com',
            'iat': now,
            'exp': now + 30,
        })
        if isinstance(token, bytes):
            token = token.decode('utf8')
        payload = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': token}
        r = requests.post("https://oauth-2-authorization-server.services.atlassian.com/oauth2/token", data=payload)
        return r.json()['access_token']

    def __unicode__(self):
        return "%s: %s" % (self.key, self.host)

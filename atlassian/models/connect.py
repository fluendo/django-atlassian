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


    def create_token(self, method, uri):
        token = atlassian_jwt.encode_token(method, uri, self.key, self.shared_secret)
        return token


    def __unicode__(self):
        return "%s: %s" % (self.key, self.host)

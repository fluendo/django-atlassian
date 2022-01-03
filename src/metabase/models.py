# -*- coding: utf-8 -*-

from django.db import models
from django_atlassian.models.connect import SecurityContext


class MetabaseConfiguration(models.Model):
    """
    Given that in confluence we can't store the metabase configuration
    as application properties, we need to store them in our own
    database system
    """

    account = models.ForeignKey(SecurityContext)
    site_url = models.CharField(max_length=256, blank=False, null=False)
    secret_key = models.CharField(max_length=256, blank=False, null=False)

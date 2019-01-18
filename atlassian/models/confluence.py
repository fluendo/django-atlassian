# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models

class Content(models.base.Model):
    """
    Base class for all Confluence content models.
    """
    PAGE_TYPE = 'page'
    BLOGPOST_TYPE = 'blogpost'
    COMMENT_TYPE = 'comment'
    ATTACHMENT_TYPE = 'attachment'

    TYPE_CHOICES = (
        (PAGE_TYPE, PAGE_TYPE),
        (BLOGPOST_TYPE, BLOGPOST_TYPE),
        (COMMENT_TYPE, COMMENT_TYPE),
        (ATTACHMENT_TYPE, ATTACHMENT_TYPE),
    )

    id = models.CharField(max_length=255, primary_key=True, unique=True)
    creator = models.CharField(max_length=255, null=False, blank=False)
    created = models.DateField()
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    title = models.TextField(null=False, blank=False)
    space = models.CharField(max_length=255, null=False, blank=False)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        abstract = True


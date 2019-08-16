# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from atlassian import models

class LabelAdmin(admin.ModelAdmin):
    pass

class ProjectAdmin(admin.ModelAdmin):
    pass

class IssueAdmin(admin.ModelAdmin):
    list_display = ['key']

class ContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']

admin.site.register(models.Label, LabelAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Issue, IssueAdmin)
admin.site.register(models.Content, ContentAdmin)

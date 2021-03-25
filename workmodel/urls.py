# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url, include

from workmodel import views

urlpatterns = [
    url(r'^initiative_status/$', views.initiative_status, name='workmodel-initiative-status'),
    url(r'^issue_versions/$', views.issue_versions, name='workmodel-issue-versions'),
    url(r'^customers-view/$', views.customers_view, name='workmodel-customers-view'),
    url(r'^customers-view-update/$', views.customers_view_update,  name='customers-view-update'),
    url(r'^customers-proxy/$', views.customers_proxy_view, name='workmodel-customers-proxy'),
    url(r'^issue-updated/$', views.issue_updated, name='workmodel-atlassian-issue-updated'),
    url(r'^issue-created/$', views.issue_created, name='workmodel-atlassian-issue-created'),
    url(r'^addon-enabled/$', views.addon_enabled, name='workmodel-addon-enabled'),
    url(r'^project-created/$', views.project_created, name='workmodel-project-created'),
    url(r'^project-updated/$', views.project_updated, name='workmodel-project-updated'),
    url(r'^project-deleted/$', views.project_deleted, name='workmodel-project-deleted'),
]

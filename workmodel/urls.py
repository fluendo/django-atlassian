# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url, include

from workmodel import views

urlpatterns = [
    url(r'^initiative_status/$', views.initiative_status, name='workmodel-initiative-status'),
    url(r'^issue_versions/$', views.issue_versions, name='workmodel-issue-versions'),
    url(r'^issue_versions-progress/$', views.issue_versions_progress, name='workmodel-issue-versions-progress'),
    url(r'^issue-updated/$', views.issue_updated, name='workmodel-issue-updated'),
    url(r'^addon-enabled/$', views.addon_enabled, name='workmodel-addon-enabled'),
    url(r'^project-created/$', views.project_created, name='workmodel-project-created'),
    url(r'^project-updated/$', views.project_updated, name='workmodel-project-updated'),
    url(r'^project-deleted/$', views.project_deleted, name='workmodel-project-deleted'),
    url(r'^business-time-configuration/$', views.business_time_configuration, name='workmodel-business-time-configuration'),
    url(r'^business-time-transitions-dashboard-item/$', views.business_time_transitions_dashboard_item, name='workmodel-business-time-transitions-dashboard-item'),
    url(r'^business-time-transitions-dashboard-item-configuration/$', views.business_time_transitions_dashboard_item_configuration, name='workmodel-business-time-transitions-dashboard-item-configuration'),
    url(r'^hierarchy-configuration/$', views.hierarchy_configuration, name='workmodel-hierarchy-configuration'),
    url(r'^update-issues-business-time/$', views.configuration_update_issues_business_time, name='workmodel-configuration-update-issues-business-time'),
]
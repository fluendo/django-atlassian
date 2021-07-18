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
    url(r'^hierarchy-list/$', views.hierarchy_list, name='workmodel-hierarchy-list'),
    url(r'^hierarchy-update-list/$', views.hierarchy_update_list, name='workmodel-hierarchy-update-list'),
    url(r'^hierarchy-configuration/(?P<id>[0-9]+)/$', views.hierarchy_configuration, name='workmodel-hierarchy-configuration'),
    url(r'^hierarchy-update-configuration/(?P<id>[0-9]+)/$', views.hierarchy_update_configuration, name='workmodel-hierarchy-update-configuration'),
    url(r'^business-time-rescan-issues-progress/$', views.business_time_rescan_issues_progress, name='workmodel-business-time-rescan-issues-progress'),
    url(r'^business-time-update-start-stop-fields/$', views.business_time_update_start_stop_fields, name='workmodel-business-time-update-start-stop-fields'),
]

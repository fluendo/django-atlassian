# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, url

from metabase import views

urlpatterns = [
    url(
        r"^jira-configuration/$",
        views.jira_configuration,
        name="metabase-jira-configuration",
    ),
    url(
        r"^dashboard-item-view/$",
        views.dashboard_item_view,
        name="metabase-dashboard-item-view",
    ),
    url(
        r"^confluence-configuration/$",
        views.ConfluenceConfiguration.as_view(),
        name="metabase-confluence-configuration-page",
    ),
    url(r"^macro-view/$", views.macro_view, name="metabase-macro-view"),
    url(
        r"^macro-configuration/$",
        views.macro_configuration,
        name="metabase-macro-configuration",
    ),
]

# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url, include

from metabase import views

urlpatterns = [
    url(r'^configuration/$', views.configuration, name='metabase-configuration-page'),
    url(r'^dashboard-item-view/$', views.dashboard_item_view, name='metabase-dashboard-item-view'),
]

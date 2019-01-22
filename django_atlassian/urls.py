# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

import views

urlpatterns = [
    url(r'^installed/$', views.installed, name='django-atlassian-installed'),
]


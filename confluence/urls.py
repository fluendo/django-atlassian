# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url, include

import views

urlpatterns = [
    # basic views
    url(r'^$', views.AppDescriptor.as_view(), name='confluence-connect-json'),
    url(r'^helloworld/$', views.helloworld, name='confluence-helloworld'),
    url(r'^initiative_status/$', views.initiative_status, name='confluence-initiative-status'),
]

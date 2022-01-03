# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url

from fluendo import views

urlpatterns = [
    url(r'^customers-view/$', views.customers_view, name='fluendo-customers-view'),
    url(r'^customers-proxy/$', views.customers_proxy_view, name='fluendo-customers-proxy'),
    url(r'^company-view/$', views.company_view, name='fluendo-company-view'),
    url(r'^company-proxy/$', views.company_proxy_view, name='fluendo-company-proxy'),
]

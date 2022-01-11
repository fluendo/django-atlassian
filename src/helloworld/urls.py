# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, url

from helloworld import views

urlpatterns = [
    url(r"^helloworld-macro/$", views.helloworld_macro, name="helloworld-macro"),
]

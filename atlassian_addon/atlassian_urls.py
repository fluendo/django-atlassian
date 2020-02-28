from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^atlassian/', include('django_atlassian.urls')),
    url(r'^atlassian/', include('atlassian.urls')),
]

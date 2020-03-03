from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^atlassian/', include('django_atlassian.urls')),
    url(r'^atlassian/', include('atlassian.urls')),
    url(r'^atlassian/jira', include('atlassian.jira_urls')),
    url(r'^atlassian/confluence', include('atlassian.confluence_urls')),
]

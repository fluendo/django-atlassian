from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^atlassian/', include('django_atlassian.urls')),
    url(r'^workmodel/', include('workmodel.urls')),
    url(r'^sales/', include('sales.urls')),
]

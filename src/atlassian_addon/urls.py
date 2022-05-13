from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^atlassian/", include("django_atlassian.urls")),
    url(r"^workmodel/", include("workmodel.urls")),
    url(r"^sales/", include("sales.urls")),
    url(r"^metabase/", include("metabase.urls")),
    url(r"^fluendo/", include("fluendo.urls")),
]
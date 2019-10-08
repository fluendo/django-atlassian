from django.conf import settings
from django.conf.urls import url, include

import views

urlpatterns = [
    # fluendo issue to customer views
    url(r'^customers-view/$',
        views.customers_view,
        name='customers-view'),
    url(r'^customers-view-update/$',
        views.customers_view_update,
        name='customers-view-update'),
    url(r'^customers-proxy/$',
        views.customers_proxy_view,
        name='customers-proxy'),
]
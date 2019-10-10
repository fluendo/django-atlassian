from django.conf import settings
from django.conf.urls import url, include

import views

urlpatterns = [
    # sales views
    url(r'^accounts/$',
        views.SalesAccountsListView.as_view(),
        name='sales-accounts-list-view'),
    url(r'^accounts/(?P<pk>[0-9]+)/$',
        views.SalesAccountDetailView.as_view(),
        name='sales-account-detail-view'),
    url(r'^contacts/$',
        views.SalesContactsListView.as_view(),
        name='sales-contacts-list-view'),
    url(r'^contacts/(?P<pk>[0-9]+)/$',
        views.SalesContactsDetailView.as_view(),
        name='sales-contacts-detail-view'),
    url(r'^contacts/add/$',
            views.SalesContactsAddView.as_view(),
            name='sales-contacts-add-view'),
    url(r'^users/$', 
        views.SalesUsersSearch.as_view(),
        name="sales-users-view"),
]
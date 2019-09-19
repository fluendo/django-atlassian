from django.conf import settings
from django.conf.urls import url, include

import views

urlpatterns = [
    # basic views
    url(r'^$', views.AppDescriptor.as_view(), name='attlasian-connect-json'),
    url(r'^helloworld/$', views.helloworld, name='atlassian-hello-world'),

    # issue updated or created
    url(r'^issue-updated/$', views.issue_updated, name='atlassian-issue-updated'),
    url(r'^issue-created/$', views.issue_created, name='atlassian-issue-created'),

    #post functions views
    url(r'^postfunction-increment-create/$',
        views.postfunction_increment_create,
        name='atlassian-postfunction-increment-create'),
    url(r'^postfunction-increment-create/(?P<workflow_conf>.*)/$',
        views.postfunction_increment_create,
        name='atlassian-postfunction-increment-create'),
    url(r'^postfunction-increment-view/$',
        views.postfunction_increment_view,
        name='atlassian-postfunction-increment-view'),
    url(r'^postfunction-increment-view/(?P<workflow_conf>.*)/$',
        views.postfunction_increment_view,
        name='atlassian-postfunction-increment-view'),
    url(r'^postfunction-increment-triggered/$',
        views.postfunction_increment_triggered,
        name='atlassian-postfunction-increment-triggered'),
    url(r'^postfunction-decrement-create/$',
        views.postfunction_decrement_create,
        name='atlassian-postfunction-decrement-create'),
    url(r'^postfunction-decrement-create/(?P<workflow_conf>.*)/$',
        views.postfunction_decrement_create,
        name='atlassian-postfunction-decrement-create'),
    url(r'^postfunction-decrement-view/$',
        views.postfunction_decrement_view,
        name='atlassian-postfunction-decrement-view'),
    url(r'^postfunction-decrement-view/(?P<workflow_conf>.*)/$',
        views.postfunction_decrement_view,
        name='atlassian-postfunction-decrement-view'),
    url(r'^postfunction-decrement-triggered/$',
        views.postfunction_decrement_triggered,
        name='atlassian-postfunction-decrement-triggered'),

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

    # sales customers views
    url(r'sales/accounts/$',
        views.SalesAccountsListView.as_view(),
        name='sales-accounts-list-view'),
    url(r'sales/accounts/(?P<pk>[0-9]+)/$',
        views.SalesAccountDetailView.as_view(),
        name='sales-account-detail-view'),
    url(r'sales/contacts/$',
        views.SalesContactsListView.as_view(),
        name='sales-contacts-list-view'),
    url(r'sales/contacts/(?P<pk>[0-9]+)/$',
        views.SalesContactsDetailView.as_view(),
        name='sales-contacts-detail-view'),
    url(r'sales/users/$', views.SalesUsersSearch.as_view(), ),

]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

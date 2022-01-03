from django.conf import settings
from django.conf.urls import url, include

from feedback import views

urlpatterns = [
    url(r'^postfunction-increment-create/$',
        views.postfunction_increment_create,
        name='feedback-increment-create'),
    url(r'^postfunction-increment-create/(?P<workflow_conf>.*)/$',
        views.postfunction_increment_create,
        name='feedback-increment-create'),
    url(r'^postfunction-increment-view/$',
        views.postfunction_increment_view,
        name='feedback-increment-view'),
    url(r'^postfunction-increment-view/(?P<workflow_conf>.*)/$',
        views.postfunction_increment_view,
        name='feedback-increment-view'),
    url(r'^postfunction-increment-triggered/$',
        views.postfunction_increment_triggered,
        name='feedback-increment-triggered'),
    url(r'^postfunction-decrement-create/$',
        views.postfunction_decrement_create,
        name='feedback-decrement-create'),
    url(r'^postfunction-decrement-create/(?P<workflow_conf>.*)/$',
        views.postfunction_decrement_create,
        name='feedback-decrement-create'),
    url(r'^postfunction-decrement-view/$',
        views.postfunction_decrement_view,
        name='feedback-decrement-view'),
    url(r'^postfunction-decrement-view/(?P<workflow_conf>.*)/$',
        views.postfunction_decrement_view,
        name='feedback-decrement-view'),
    url(r'^postfunction-decrement-triggered/$',
        views.postfunction_decrement_triggered,
        name='feedback-decrement-triggered'),

]



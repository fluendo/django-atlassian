from django.conf import settings
from django.conf.urls import url, include

urlpatterns = [
    # customers
    url(r'', include('customers.urls')),

    # sales urls & views
    url(r'^sales/', include('sales.urls')),
]
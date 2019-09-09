import json
import requests
import operator

from django.conf import settings
from django.http import JsonResponse, Http404

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import cache_page


# Cache time to live is 5 minutes.
CACHE_TTL = 60 * 5
@cache_page(CACHE_TTL)
def customers_proxy_cache(request):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customers/'
    r = requests.get(api_url, headers=web_auth)
    data = sorted(r.json(), key=operator.itemgetter('company_name'))
    return JsonResponse(data, safe=False)

@xframe_options_exempt
def customer_by_id_proxy(request, pk):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customers/' + pk
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False)

@xframe_options_exempt
def agreements_by_account_id(request, agreement_pk, account_pk=None):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/agreements/' + str(agreement_pk)
    if account_pk:
        api_url += "/?account_pk={pk}".format(pk=account_pk)
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False)

@xframe_options_exempt
def account_contacts_by_pk(request, contact_pk):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customer-contacts/'
    if contact_pk:
        api_url += "{pk}/".format(pk=contact_pk)
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False) 
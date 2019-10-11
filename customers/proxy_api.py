import json
import requests
import operator

from django.conf import settings
from django.http import JsonResponse, Http404

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import cache_page


def customers_proxy(request):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customers/?limit=200'
    r = requests.get(api_url, headers=web_auth)
    if r.status_code == 200:
        if type(r.json()) == dict:
            request_data = r.json()['results']
        elif type(r.json()) == list:
            request_data = r.json()
        data = sorted(
            request_data,
            key=operator.itemgetter('company_name')
        )
    else:
        data = None
    return JsonResponse(data, safe=False)

# Cache time to live is 5 minutes.
CACHE_TTL = 60 * 5
@cache_page(CACHE_TTL)
def customers_proxy_cache(request):
    return customers_proxy(request)

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
    api_url = settings.WEB_FLUENDO_API_SERVER + '/customers/contacts/'
    if contact_pk:
        api_url += "{pk}/".format(pk=contact_pk)
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False) 

@xframe_options_exempt
def patch_account(account_pk, json_data):
    if account_pk:
        web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
        api_url_str = settings.WEB_FLUENDO_API_SERVER + '/customers/{pk}/'
        api_url = api_url_str.format(pk=account_pk)
        data = requests.patch(api_url, headers=web_auth, json=json_data)
        return data
    else:
        return False

def contacts_proxy(request):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/contacts/'
    r = requests.get(api_url, headers=web_auth)
    data = sorted(r.json(), key=operator.itemgetter('created_at'))
    return JsonResponse(data, safe=False)

def contacts_proxy_post(data):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN,
    'Content-type': 'application/json'}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/contacts/'
    r = requests.post(api_url, data=data, headers=web_auth)
    return JsonResponse(r.status_code, safe=False)


@xframe_options_exempt
def contact_by_id_proxy(request, pk):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/contacts/' + pk
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False)

@xframe_options_exempt
def contact_proxy_patch(contact_pk, data):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN,
                'Content-Type': 'application/json'}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/contacts/{}/'
    api_url = api_url.format(contact_pk)
    r = requests.patch(api_url, data=data, headers=web_auth)
    data = r.json()
    return JsonResponse(data, status=r.status_code, reason=r.reason, safe=False)

@xframe_options_exempt
def user_proxy(search):
    web_auth = {'Authorization': 'Token ' + settings.WEB_FLUENDO_TOKEN,
                'Content-Type': 'application/json'}
    api_url = settings.WEB_FLUENDO_API_SERVER + '/users/?q={}'
    api_url = api_url.format(search)
    r = requests.get(api_url, headers=web_auth)
    data = r.json()
    return JsonResponse(data, safe=False)

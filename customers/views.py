from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django_atlassian.decorators import jwt_required

from proxy_api import customers_proxy_cache


@csrf_exempt
@jwt_required
@xframe_options_exempt
def customers_view(request):
    Issue = request.atlassian_model
    key = request.GET.get('key')
    property_key = 'customers'
    issue = None
    customers_json = None

    if key:
        issue = Issue.objects.get(key=key)

    customers = customers_proxy_cache(request)
    if customers:
        customers_json = json.loads(customers.content)

    if key and issue and customers:
        try:
            customer_property = Issue.jira.issue_property(
                issue, property_key)
        except:
            customer_property = {
                'value':{
                    'customer': 'click to choose one',
                    'customer_id': 0,
                }
            }

        rest_url = '/rest/api/2/issue/' + issue.key + '/properties/customers'
        return render(
            request,
            'customers_view.html',
            {
                'issue': issue,
                'rest_url': rest_url,
                'customers': customers_json,
                'c_property': customer_property,
            })
    else:
        return HttpResponseBadRequest()


@xframe_options_exempt
def customers_proxy_view(request):
    return customers_proxy_cache(request)


@csrf_protect
def customers_view_update(request):
    try:
        Issue = request.atlassian_model
    except:
        from atlassian.models import Issue

    issue_key = request.GET.get('issue_key')
    property_key = 'customers'
    issue = None
    data = json.loads(request.body)
    customer = data['customer']
    customer_id = data['customer_id']

    if issue_key:
        issue = Issue.objects.get(key=issue_key)
        Issue.jira.add_issue_property(
            issue_key,
            property_key,
            {
                'customer': customer,
                'customer_id': customer_id
            }
        )

    return HttpResponse(status=200)

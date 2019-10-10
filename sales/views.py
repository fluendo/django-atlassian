import json

from django.views.generic.base import TemplateView, View
from django.views.generic import CreateView
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.contrib import messages

from django_atlassian.decorators import jwt_required

from customers.proxy_api import (
    agreements_by_account_id,
    customer_by_id_proxy,
    customers_proxy_cache,
    contact_by_id_proxy,
    contacts_proxy,
    contact_proxy_patch,
    account_contacts_by_pk,
    user_proxy,
    patch_account
)

from atlassian.forms import (
    AccountForm,
    ContactForm
)


class SalesAccountsListView(View):
    template_name = 'sales/accounts-list-view.html'

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        accounts = customers_proxy(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'accounts': json.loads(accounts.content)}
        )


class SalesAccountDetailView(View):
    template_name = 'sales/account-detail.html'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            account_json = customer_by_id_proxy(request, account_pk)
            account = json.loads(account_json.content)

            agreements = []
            for agreement_pk in account['reselleragreement_set']:
                agreements_json = agreements_by_account_id(request, agreement_pk)
                agreements += [json.loads(agreements_json.content)]

            contacts = []
            for contact_pk in account['customercontact_set']:
                contacts_json = account_contacts_by_pk(request,contact_pk)
                contacts += [json.loads(contacts_json.content)]

            account_form = AccountForm(initial=account)

            return render(
                request,
                self.template_name,
                {
                    'account_form': account_form,
                    'account': account,
                    'agreements': agreements,
                    'contacts': contacts,
                }
            )
        else:
            raise Http404()

    @method_decorator(xframe_options_exempt, csrf_protect)
    def post(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            form = AccountForm(
                data=request.POST,
                initial=request.POST)
            if form.is_valid():
                form.fix_boolean_fields()
                json_data = form.cleaned_data
                response = patch_account(account_pk, json_data)
                if response.status_code == 200:
                        messages.success(
                            request,
                            str(response.status_code) + ': OK' #+ response.text
                        )
                else:
                    messages.warning(
                        request,
                        str(response.status_code) + ': ' + response.text
                    )
            else:
                messages.error('form data error')
                return redirect('sales-account-detail-view', pk=account_pk)
        else:
            return Http404()
        return redirect('sales-account-detail-view', pk=account_pk)




    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        return user_proxy(search)

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


class SalesAccountsListView(View):
    template_name = 'sales/accounts-list-view.html'

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        accounts = customers_proxy_cache(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'accounts': json.loads(accounts.content)}
        )


class SalesAccountDetailView(View):
    template_name = 'sales/account-detail.html'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            account_json = customer_by_id_proxy(request, account_pk)
            account = json.loads(account_json.content)
            
            agreements = []
            for agreement_pk in account['reselleragreement_set']:
                agreements_json = agreements_by_account_id(request, agreement_pk)
                agreements += [json.loads(agreements_json.content)]

            contacts = []
            for contact_pk in account['customercontact_set']:
                contacts_json = account_contacts_by_pk(request,contact_pk)
                contacts += [json.loads(contacts_json.content)]

            account_form = AccountForm(initial=account)

            return render(
                request,
                self.template_name,
                {
                    'account_form': account_form,
                    'account': account,
                    'agreements': agreements,
                    'contacts': contacts,
                }
            )
        else:
            raise Http404()
    
    @method_decorator(xframe_options_exempt, csrf_protect)
    def post(self, request, *args, **kwargs):
        account_pk = kwargs.get('pk', None)
        if account_pk:
            form = AccountForm(
                data=request.POST,
                initial=request.POST)
            if form.is_valid():
                form.fix_boolean_fields()
                json_data = form.cleaned_data
                response = patch_account(account_pk, json_data)
                if response.status_code == 200:
                        messages.success(
                            request,
                            str(response.status_code) + ': OK' #+ response.text
                        )
                else:
                    messages.warning(
                        request,
                        str(response.status_code) + ': ' + response.text
                    )
            else:
                messages.error('form data error')
                return redirect('sales-account-detail-view', pk=account_pk)
        else:
            return Http404()
        return redirect('sales-account-detail-view', pk=account_pk)


class SalesContactsListView(View):
    template_name = 'sales/contact-list-view.html'

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        contacts = contacts_proxy(request, *args, **kwargs)
        return render(
            request,
            self.template_name,
            {'contacts': json.loads(contacts.content)}
        )


class SalesContactsDetailView(View):
    template_name = "sales/contact-detail-view.html"
    form_class = ContactForm

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        contact_pk = kwargs.get('pk', None)

        if contact_pk:
            contact_json = contact_by_id_proxy(request, contact_pk)
            contact = json.loads(contact_json.content) 
            return render(
                request,
                self.template_name,
                {
                    'form': self.form_class(initial=contact),
                }
            )
        else:
            raise Http404()

    @method_decorator(xframe_options_exempt, jwt_required)
    def post(self, request, *args, **kwargs):
        contact_pk = kwargs.get('pk', None) 
        form = self.form_class(request.POST)
        if contact_pk:
            if form.is_valid():
                contact_json = json.dumps(form.cleaned_data)
                response = contact_proxy_patch(contact_pk, contact_json)
                if response.status_code == 200:
                    messages.success(
                        request,
                        str(response.status_code) + ': OK' #+ response.text
                    )
                else:
                    messages.warning(
                        request,
                        str(response.status_code) + ': ' + response.content
                    )
            else:
                messages.error(request, str(form.errors))
        else:
            raise Http404()
        return redirect('sales-contacts-detail-view', pk=contact_pk)


class SalesContactsAddView(CreateView):
    template_name = "sales/contact-add-view.html"
    form_class = ContactForm

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {
                'form': self.form_class()
            }

        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            contact_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
            }
            response = contacts_proxy_post(contact_data)
            if response.status_code == 204:
               messages.success(
                   request,
                   str(response.status_code) + ': Created' #+ response.text
               )
            else:
               messages.warning(
                   request,
                   str(response.status_code) + ': ' + response.reason_phrase
               )
        else:
            messages.error(request, str(form.errors))
            return render(
                        request,
                        self.template_name,
                        {
                            'form': self.form_class()
                        }
            )
        return redirect('sales-contacts-list-view')


class SalesUsersSearch(View):

    @method_decorator(xframe_options_exempt, jwt_required)
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        return user_proxy(search)
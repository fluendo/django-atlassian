from django import forms

class AccountForm(forms.Form):
    company_name = forms.CharField()
    street = forms.CharField()
    city = forms.CharField()
    phone = forms.CharField()
    email = forms.EmailField()
    postal_code = forms.CharField()
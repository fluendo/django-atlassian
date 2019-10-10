from django import forms
from django_countries.fields import CountryField

class AutoForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial:
            for k,v in initial.items():
                if k not in self.exclude:
                    if type(v) == int:
                        self.fields[k] = forms.IntegerField(
                            required=False)
                        self.fields[k].widget.attrs['class'] = 'text'
                    elif type(v) in (type(True), type(False)):
                        self.fields[k] = forms.BooleanField(
                            initial=True, required=False)
                        self.fields[k].widget.attrs['class'] = ''
                    else:
                        self.fields[k] = forms.CharField(
                            required=False)
                        self.fields[k].widget.attrs['class'] = 'text medium-long-field'


class AccountForm(AutoForm):
    exclude = ['id', 'contact', 'contacts', 'agreements']
    boolean_fields = ['show_welcome', 'enable_send_mails']
    groups = {
        'info':[
            'street',
            'postal_code',
            'city',
            'vat',
            'company_name',
            'fax',
            'phone',
            'web',
        ],
        'billing': [
            'billing_street',
            'billing_company_name',
            'billing_country',
            'billing_postal_code',
            'billing_city',
        ],
        'others': [
            'fluendo_company',
            'show_welcome',
            'num_employees',
            'enable_send_mails',
            'user',
        ],
    }

    def fix_boolean_fields(self):
        for k in self.boolean_fields:
            field = self.cleaned_data.get(k)
            if field:
                self.cleaned_data[k] = True
            else:
                self.cleaned_data[k] = False


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=200, label="First Name",
     widget=forms.TextInput(
            attrs={
             'placeholder': 'First Name',
             'id': 'first_name'}
        )
    )
    last_name = forms.CharField(max_length=200, label="Last Name",
    widget=forms.TextInput(
        attrs={
         'placeholder': 'Last Name',
         'id': 'last_name'}
        )
    )
    email = forms.EmailField(max_length=254, label="Email",
     widget=forms.EmailInput(
        attrs={
         'placeholder': 'Email',
         'id': 'email'}
        )
    )

    note = forms.CharField(label="Recent Note", required=False,
        widget=forms.Textarea(
            attrs={
             'placeholder': 'Recent Note',
             'rows': 90,
             'cols': 90,
             'id': 'note'}
            )
    )

    user = forms.IntegerField(label="User", required=False,
     widget=forms.TextInput(
        attrs={
         'placeholder': 'User',
         'id': 'user'}
        )
    )
    tags = forms.CharField(label='Tags', max_length=100, required=False,
      widget=forms.TextInput(
        attrs={
         'placeholder': 'Tags',
         'id': 'tags'
         }
        )   
    )
    job_title = forms.CharField(label='Job Title', max_length=150, required=False,
       widget=forms.TextInput(
        attrs={
         'placeholder': 'Job title',
         'id': 'job_title'}
        )   
    ) 
    department = forms.CharField(label='Department', max_length=200, required=False,
       widget=forms.TextInput(
        attrs={
         'placeholder': 'Department',
         'id': 'department'
         }
        )   
    )
    country = CountryField().formfield(
        widget=forms.Select(
            attrs={
                'placeholder': 'Country',
                'id': 'country'
            }
        )
    )
    street = forms.CharField(label="Street address", max_length=160, required=False,
       widget=forms.TextInput(
        attrs={
         'placeholder': 'Street',
         'id': 'street'}
        )
    )
    state = forms.CharField(label="State", max_length=100, required=False,
        widget=forms.TextInput(
        attrs={
         'placeholder': 'State',
         'id': 'state'}
        )   
    )
    city = forms.CharField(label="City", max_length=100, required=False, 
        widget=forms.TextInput(
        attrs={
         'placeholder': 'City',
         'id': 'city'}
        )
    )
    postal_code = forms.CharField(label="Postal/ZIP code", max_length=10, required=False,
        widget=forms.TextInput(
        attrs={
         'placeholder': 'Postal Code',
         'id': 'postal_code'}
        )   
    )
    phone_work = forms.CharField(label='Work phone', max_length=50, required=False,
        widget=forms.TextInput(
        attrs={
         'placeholder': 'Work phone',
         'id': 'phone_work'}
        )    
    )
    phone_mobile = forms.CharField(label='Mobile phone', max_length=50, required=False,
      widget=forms.TextInput(
        attrs={
         'placeholder': 'Mobile phone',
         'id': 'phone_mobile'}
        )    
    )
    active = forms.BooleanField(initial=True, required=False)

    instagram = forms.CharField(label='Instagram', max_length=150, required=False,
        widget=forms.TextInput(
            attrs={'class': 'text medium-long-field',
                'placeholder': 'Instagram',
                'id': 'instagram' 
            }
        ) 
    )
    facebook = forms.CharField(label='Facebook', max_length=150, required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Facebook',
                'id': 'facebook' 
            }
        ) 
    )
    twitter = forms.CharField(label='Twitter', max_length=150, required=False,
         widget=forms.TextInput(
            attrs={
                'placeholder': 'Twitter',
                'id': 'twitter' 
            }
        )   
    )
    linkedin = forms.CharField(label='Linkedin', max_length=150, required=False,
          widget=forms.TextInput(
            attrs={
                'placeholder': 'Linkedin',
                'id': 'linkedin' 
            }
        )   
    )
    web = forms.CharField(label='Web site', max_length=150, required=False,
         widget=forms.TextInput(
             attrs={
                 'placeholder': 'Web site',
                 'id': 'web'
             }
         )
    )

    groups = {
        'info': [
            'first_name',
            'last_name',
            'email',
            'user',
            'tags',
            'note',
            'active'
        ],
        'Telephone': [
            'phone_work',
            'phone_mobile',
        ],
        'work': [
            'job_title',
            'department',
        ],
        'address': [
            'country',
            'city',
            'state',
            'street',
            'postal_code'
        ],
        'social': [
            'instagram',
            'facebook',
            'twitter',
            'web'
        ]
    }
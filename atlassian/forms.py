from django import forms


class AutoForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial:
            for k,v in initial.items():
                if k not in self.exclude:
                    if type(v) == int:
                        self.fields[k] = forms.IntegerField()
                        self.fields[k].widget.attrs['class'] = 'text'
                    elif type(v) in (type(True), type(False)):
                        self.fields[k] = forms.BooleanField()
                        self.fields[k].widget.attrs['class'] = ''
                    else:
                        self.fields[k] = forms.CharField()
                        self.fields[k].widget.attrs['class'] = 'text medium-long-field'


class AccountForm(AutoForm):
    exclude = ['id', 'contact', 'contacts', 'agreements']
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


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=200, label="First Name")
    last_name = forms.CharField(max_length=200, label="Last Name")
    email = forms.EmailField(max_length=254, label="Email")
    user = forms.IntegerField(label="User")


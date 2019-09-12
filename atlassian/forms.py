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
                    else:
                        self.fields[k] = forms.CharField()


class AccountForm(AutoForm):
    exclude = ['id', 'contact', 'contacts', 'agreements']
    pass


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=200, label="First Name")
    last_name = forms.CharField(max_length=200, label="Last Name")
    email = forms.EmailField(max_length=254, label="Email")
    user = forms.IntegerField(label="User")


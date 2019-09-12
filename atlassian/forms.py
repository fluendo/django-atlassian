from django import forms


class AutoForm(forms.Form):

    def __init__(self, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
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
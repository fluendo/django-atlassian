from django import forms


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=200, label="First Name")
    last_name = forms.CharField(max_length=200, label="Last Name")
    email = forms.EmailField(max_length=254, label="Email")
    user = forms.IntegerField(label="User")
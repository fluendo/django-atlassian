from django import forms

class HierarchyForm(forms.Form):
    is_operative = forms.BooleanField(required=False)
    is_container = forms.BooleanField(required=False)
    type = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select'}),
        choices=[('custom', 'Custom'), ('epic', 'Epic'), ('sub-task', 'Sub-Task')]
    )
    issues = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'class': 'select selector-ui', 'multiple': 'multiple'}),
        required=False, choices=[]
    )
    field = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select'}),
        required=False, choices=[]
    )
    link = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select'}),
        required=False, choices=[]
    )

    def __init__(self, *args ,**kwargs):
        hierarchy_service = kwargs.pop('hierarchy_service')
        if not hierarchy_service:
            raise ValueError
        self.hierarchy_service = hierarchy_service

        super(HierarchyForm, self).__init__(*args, **kwargs)

        self.fields['issues'].choices = [(x.id, x.name) for x in self.hierarchy_service.addon_jira.issue_types()]
        self.fields['field'].choices = [(x['key'], x['name']) for x in self.hierarchy_service.addon_jira.fields()] + [('', 'None')]
        self.fields['link'].choices = [(x.id, x.name) for x in self.hierarchy_service.addon_jira.issue_link_types()] + [('', 'None')]

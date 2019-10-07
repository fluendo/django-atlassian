from django import template

register = template.Library()

@register.filter
def none_to_empty_str(value):
    """ Set a none value to an empty string,
    this used for forms
    """
    if value == None:
        value = ""
    return value
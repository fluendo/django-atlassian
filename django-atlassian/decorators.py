# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied

def jwt_required(function):
    def decorator(request, *args, **kwargs):
        sc = getattr(request, 'atlassian_sc', None)
        model = getattr(request, 'atlassian_model', None)
        if not sc or not model:
            raise PermissionDenied
        else:
            return function(request, *args, **kwargs)
    return decorator

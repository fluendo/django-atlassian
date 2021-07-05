# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import wraps

def jwt_required(view_func):
    def decorator(*args, **kwargs):
        return view_func(*args, **kwargs)
    decorator.jwt_required = True
    return wraps(view_func)(decorator)

def jwt_qsh_exempt(view_func):
    """Mark a view function as being exempt from the qsh claim protection."""
    def decorator(*args, **kwargs):
        return view_func(*args, **kwargs)
    decorator.jwt_qsh_exempt = True
    return wraps(view_func)(decorator)

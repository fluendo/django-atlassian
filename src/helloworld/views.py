# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.decorators.clickjacking import xframe_options_exempt
from django.shortcuts import render

@xframe_options_exempt
def helloworld_macro(request):
    return render(request, 'helloworld/macro.html')

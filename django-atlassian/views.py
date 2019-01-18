# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import jwt

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from models.connect import SecurityContext

@csrf_exempt
def installed(request):
    """
    Main view to handle the signal of the cloud instance when the addon
    has been installed
    """
    try:
        post = json.loads(request.body)
        key = post['key']
        shared_secret = post['sharedSecret']
        client_key = post['clientKey']
        host = post['baseUrl']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest()

    # Store the security context
    # https://developer.atlassian.com/cloud/jira/platform/authentication-for-apps/
    sc = SecurityContext.objects.filter(key=key, host=host).first()
    if sc:
        update = False
        # Confirm that the shared key is the same, otherwise update it
        if sc.shared_secret != shared_secret:
            sc.shared_secret = shared_secret
            update = True
        if sc.client_key != client_key:
            sc.client_key = client_key
            update = True
        if update:
            sc.save()
    else:
        # Create a new entry on our database of connections
        sc = SecurityContext()
        sc.key = key
        sc.host = host
        sc.shared_secret = shared_secret
        sc.client_key = client_key
        sc.save()

    return HttpResponse(status=204)

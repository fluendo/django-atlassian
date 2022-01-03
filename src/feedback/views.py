# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.decorators.clickjacking import xframe_options_exempt
from django_atlassian.decorators import jwt_required
from atlassian.models import Issue
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@jwt_required
@xframe_options_exempt
def increment_create(request, workflow_conf=None):
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.get_internal_type() == 'FloatField':
            numeric_fields.append(f)
        if f.name == workflow_conf:
            field = f
    data = {
        'fields': numeric_fields,
        'field': field
    }
    return render(request, 'feedback/increment_create.html', data)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def increment_view(request, workflow_conf=None):
    # get the verbose name from the field
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.name == workflow_conf:
            field = f
            break

    return render(request, 'feedback/increment_view.html', {'field': field})


@csrf_exempt
@jwt_required
@xframe_options_exempt
def decrement_view(request, workflow_conf=None):
    # get the verbose name from the field
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.name == workflow_conf:
            field = f
            break

    return render(request, 'feedback/decrement_view.html', {'field': field})


@csrf_exempt
@jwt_required
def decrement_triggered(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    field = body['configuration']['value']
    try:
        value = getattr(i, field)
        if not value:
            value = 0
        value = value - 1
        if value < 0:
            value = 0
        setattr(i, field, value)
        i.save(update_fields=[field])
    except:
        return HttpResponseBadRequest()
    return HttpResponse(204)




@csrf_exempt
@jwt_required
def increment_triggered(request):
    Issue = request.atlassian_model
    body = json.loads(request.body)
    i = Issue.objects.create_from_json(body['issue'])
    field = body['configuration']['value']
    try:
        value = getattr(i, field)
        if not value:
            value = 0
        value = value + 1
        setattr(i, field, value)
        i.save(update_fields=[field])
    except:
        return HttpResponseBadRequest()
    return HttpResponse(204)


@csrf_exempt
@jwt_required
@xframe_options_exempt
def decrement_create(request, workflow_conf=None):
    Issue = request.atlassian_model
    numeric_fields = []
    field = None
    for f in Issue._meta.fields:
        if f.get_internal_type() == 'FloatField':
            numeric_fields.append(f)
        if f.name == workflow_conf:
            field = f
    data = {
        'fields': numeric_fields,
        'field': field
    }
    return render(request, 'feedback/decrement_create.html', data)

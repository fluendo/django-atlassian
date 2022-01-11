# -*-  coding: utf-8 -*-
from django import template

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def div(value, arg):
    return value / arg


@register.filter
def sum(value, arg):
    return value + arg


@register.filter
def modulo(value, arg):
    return value % arg

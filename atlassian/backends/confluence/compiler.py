# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_atlassian.backends.common import compiler

class SQLCompiler(compiler.SQLCompiler):
    query_param = 'cql'

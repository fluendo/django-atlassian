# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_atlassian.backends.common import compiler as common_compiler
from django.db.models.sql import compiler

class SQLCompiler(common_compiler.SQLCompiler):
    query_param = 'jql'


class SQLUpdateCompiler(SQLCompiler):
    def as_sql(self):
        # Generate the json to update
        values = {}
        for field, model, val in self.query.values:
            if hasattr(val, 'resolve_expression'):
                val = val.resolve_expression(self.query, allow_joins=False, for_save=True)
                if val.contains_aggregate:
                    raise FieldError("Aggregate functions are not allowed in this query")
            elif hasattr(val, 'prepare_database_save'):
                if field.remote_field:
                    val = field.get_db_prep_save(
                        val.prepare_database_save(field),
                        connection=self.connection,
                    )
                else:
                    raise TypeError(
                        "Tried to update field %s with a model instance, %r. "
                        "Use a value compatible with %s."
                        % (field, val, field.__class__.__name__)
                    )
            else:
                val = field.get_db_prep_save(val, connection=self.connection)
            name = field.column
            if hasattr(val, 'as_sql'):
                sql, params = self.compile(val)
                values[name] = sql
            else:
                values[name] = val 
            
        sql, params = super(SQLUpdateCompiler, self).as_sql()
        params += tuple([{'update_fields': values}])
        return sql, params


    def execute_sql(self, result_type):
        cursor = super(SQLUpdateCompiler, self).execute_sql(result_type)
        try:
            rows = cursor.rowcount if cursor else 0
            is_empty = cursor is None
        finally:
            if cursor:
                cursor.close()
        return rows

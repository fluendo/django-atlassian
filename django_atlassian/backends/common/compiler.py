# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models.sql import compiler
from django.db.models.expressions import Col
from django.db.models.aggregates import Count
from django.db.models.fields.related_lookups import RelatedExact

class SQLCompiler(compiler.SQLCompiler):

    def compile(self, node, select_format=False):
        # A column must not have a table.column form
        if type(node) == Col:
            return '%s' % node.target.column, []
        # Skip the Count
        elif type(node) == Count:
            return '', [{'count_only': True}]
        return super(SQLCompiler, self).compile(node, select_format)

    def as_sql(self, with_limits=True, with_col_aliases=False):
        """
        Creates the SQL for this query. Returns the SQL string and list of
        parameters.

        If 'with_limits' is False, any limit/offset information is not included
        in the query.
        """
        refcounts_before = self.query.alias_refcount.copy()
        try:
            extra_select, order_by, group_by = self.pre_sql_setup()

            # This must come after 'select', 'ordering', and 'distinct' -- see
            # docstring of get_from_clause() for details.
            from_, f_params = self.get_from_clause()

            where, w_params = self.compile(self.where) if self.where is not None else ("", [])
            having, h_params = self.compile(self.having) if self.having is not None else ("", [])


            # [J,C]QL doesn't support any combinator
            if self.query.combinator:
                raise DatabaseError('{} not supported on this database backend.'.format(combinator))
            params = []

            out_cols = []
            for _, (s_sql, s_params), alias in self.select + extra_select:
                params.extend(s_params)
                out_cols.append(s_sql)

            if out_cols:
                params.extend([{'fields': ','.join(out_cols)}])

            # JQL doesn't support a select for update
            if self.query.select_for_update:
                raise TransactionManagementError('select_for_update cannot be used outside of a transaction.')

            sql = ''
            if where:
                sql += where + ' '
                params.extend(w_params)

            # JQL doesn't support group by
            if group_by:
                raise DatabaseError('GROUP BY is not supported on this database backend.')

            if having:
                raise DatabaseError('HAVING is not supported on this database backend.')

            if order_by:
                ordering = []
                for _, (o_sql, o_params, _) in order_by:
                    ordering.append(o_sql)
                    params.extend(o_params)
                sql += 'ORDER BY %s' % ', '.join(ordering)

            if with_limits:
                if self.query.high_mark is not None:
                    params.extend([{'max_results': self.query.high_mark - self.query.low_mark}])
                if self.query.low_mark:
                    params.extend([{'start_at': self.query.low_mark}])
            return "%s=%s" % (self.query_param, sql), tuple(params)
        finally:
            # Finally do cleanup - get rid of the joins we created above.
            self.query.reset_refcounts(refcounts_before)

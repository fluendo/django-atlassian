# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db.models import fields

class ArrayField(fields.Field):

    def from_jira(self, value, connection):
        return [x.decode(connection.charset) for x in value]

    def get_db_prep_save(self, value, connection):
        if not value:
            return None
        return [x.encode(connection.charset) for x in value]

    def from_db_value(self, value, expression, connection, context):
        """Convert from the database format.

        This should be the inverse of self.get_prep_value()
        """
        return self.to_python(value)

    def to_python(self, value):
        if not value:
            return []
        return value


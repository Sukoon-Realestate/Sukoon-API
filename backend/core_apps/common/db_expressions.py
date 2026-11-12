"""Portable canonical UUID text for joins to server-owned JSON evidence."""

from django.db.models import CharField, Func


class CanonicalUUIDText(Func):
    arity = 1
    output_field = CharField()

    def as_postgresql(self, compiler, connection, **extra):
        sql, params = compiler.compile(self.source_expressions[0])
        return f"({sql})::text", params

    def as_sqlite(self, compiler, connection, **extra):
        sql, params = compiler.compile(self.source_expressions[0])
        parts = [f"substr({sql}, {start}, {size})" for start, size in ((1, 8), (9, 4), (13, 4), (17, 4), (21, 12))]
        return "(" + " || '-' || ".join(parts) + ")", params * 5

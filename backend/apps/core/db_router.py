"""Router de leitura para réplica Postgres (T-P.5 / ADR-0008)."""

from __future__ import annotations


class PrimaryReplicaRouter:
    """
    Envia leituras para `replica` quando DATABASE_READ_REPLICA_URL está configurada.
    Escritas e migrações ficam no `default` (primary).
    """

    replica_name = "replica"

    def db_for_read(self, model, **hints):
        from django.conf import settings

        if self.replica_name in getattr(settings, "DATABASES", {}):
            return self.replica_name
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        db_list = {"default", self.replica_name}
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"

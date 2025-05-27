# config/db_router.py
from applications.core.db_context import get_current_camp
from applications.core.constants import CAMP_APPS, CENTRAL_APPS


class CampRouter:
    """
    Redirige operaciones a la base del campamento si está activa, o a default.
    Controla qué apps deben migrarse en cada base.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label in CAMP_APPS:
            camp = get_current_camp()
            return camp.db_name if camp else "default"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in CAMP_APPS:
            camp = get_current_camp()
            return camp.db_name if camp else "default"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migrar apps centrales solo en default
        if app_label in CENTRAL_APPS:
            return db == "default"

        # Migrar apps de campamento solo en su respectiva base
        if app_label in CAMP_APPS:
            return db != "default"

        # Otras apps (como admin, auth...) solo en default
        return db == "default"

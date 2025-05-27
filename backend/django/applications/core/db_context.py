# applications/core/db_context.py
import threading

_camp_context = threading.local()


def set_current_camp(camp):
    _camp_context.camp = camp


def get_current_camp():
    return getattr(_camp_context, "camp", None)

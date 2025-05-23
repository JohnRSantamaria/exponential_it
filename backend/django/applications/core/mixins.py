# core/mixins.py
from rest_framework import viewsets


class ReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Para vistas de solo lectura"""

    pass

# core/permissions.py
from rest_framework.permissions import BasePermission


class IsCoordinator(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "coordinator", False)

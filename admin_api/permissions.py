"""
Admin API Permissions - Require staff/superuser access
"""
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Only allow staff or superusers to access admin API endpoints.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )


class IsSuperUser(BasePermission):
    """
    Only allow superusers (stricter than staff).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )

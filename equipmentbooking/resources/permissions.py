from rest_framework import permissions


class IsResourceManagerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Allows any authenticated user to read (GET, HEAD, OPTIONS),
    but restricts write actions to resource_manager and admin roles.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.role in ['resource_manager', 'admin']

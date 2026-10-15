from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user):
    # Django Admin access already depends on is_staff, so it doubles as the
    # application's admin flag here.
    return bool(user and user.is_authenticated and user.is_staff)


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Reading is public. Creating requires a logged-in user.
    Changing or deleting requires the recipe's owner or an admin.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == request.user.pk or is_admin(request.user)

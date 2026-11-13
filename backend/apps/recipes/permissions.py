from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user):
    """Application admins may edit or delete any recipe (Issue #67).

    That's an active application user with is_admin set, which is the same
    flag GET /api/auth/me/ reports. Django staff (is_staff, who can use the
    /admin/ site) still count as well.
    """
    if not (user and user.is_authenticated):
        return False
    if user.is_staff:
        return True
    try:
        account = user.application_user
    except ObjectDoesNotExist:
        return False
    return account.is_admin and account.account_status == account.AccountStatus.ACTIVE


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

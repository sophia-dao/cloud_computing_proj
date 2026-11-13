from django.urls import path

from .views import CurrentUserView

# Mounted at /api/auth/ in config/urls.py.
#
# GET /api/auth/me/ is what the frontend calls after Cognito sign-in (PR #74).
# It returns the same body as GET /api/users/me/:
#   {"id", "email", "display_name", "profile_image", "is_admin"}
# It is read-only here. Profile edits stay on PATCH /api/users/me/.
urlpatterns = [
    path(
        "me/",
        CurrentUserView.as_view(http_method_names=["get", "head", "options"]),
        name="auth-me",
    ),
]

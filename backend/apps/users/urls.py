
from django.urls import path

from .views import (
    CurrentUserView,
    CurrentUserPreferencesView,
    CurrentUserAllergiesView,
)

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path(
        "me/preferences/",
        CurrentUserPreferencesView.as_view(),
        name="current-user-preferences",
    ),
    path(
        "me/allergies/",
        CurrentUserAllergiesView.as_view(),
        name="current-user-allergies",
    ),
]

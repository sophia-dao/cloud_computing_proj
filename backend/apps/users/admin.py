
from django.contrib import admin

from .models import (
    User,
    UserProfile,
    Tag,
    Allergen,
    UserPreference,
    UserAllergy,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "auth_user",
        "account_status",
        "is_admin",
        "created_at",
    )
    list_filter = ("account_status", "is_admin")
    search_fields = (
        "auth_user__username",
        "auth_user__email",
        "cognito_subject",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = [UserProfileInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tag")


@admin.register(UserAllergy)
class UserAllergyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "allergen")


from django.conf import settings
from django.db import models


class User(models.Model):
    """Application user linked to Django's authentication system."""

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        DISABLED = "DISABLED", "Disabled"

    auth_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application_user",
    )

    # Will be populated when Cognito integration is implemented.
    cognito_subject = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User #{self.pk}"


class UserProfile(models.Model):
    """Additional profile information for an application user."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    display_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    profile_image_reference = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Profile for User #{self.user_id}"


class Allergen(models.Model):
    """Canonical allergens shared across the application."""

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserPreference(models.Model):
    """Connects an application user to a preference tag."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="preferences",
    )

    tag = models.ForeignKey(
        "recipes.Tag",
        on_delete=models.PROTECT,
        related_name="user_preferences",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tag"],
                name="unique_user_tag_preference",
            )
        ]

    def __str__(self):
        return f"User #{self.user_id}: {self.tag}"


class UserAllergy(models.Model):
    """Connects an application user to an allergen."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="allergies",
    )

    allergen = models.ForeignKey(
        Allergen,
        on_delete=models.PROTECT,
        related_name="user_allergies",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "allergen"],
                name="unique_user_allergen",
            )
        ]

    def __str__(self):
        return f"User #{self.user_id}: {self.allergen}"

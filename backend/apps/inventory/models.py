"""
Inventory models (Issue #5).

Answers "What canonical ingredients does this registered user currently have?"
It does NOT decide which recipes the user can make; that belongs to the
recommendations app.

Fields follow docs/database-design.md section 8.
"""

from django.conf import settings
from django.db import IntegrityError, models, transaction


class InventoryItemManager(models.Manager):
    def for_user(self, user):
        """One user's inventory, with ingredient data loaded in the same query."""
        return (
            self.filter(user=user)
            .select_related("ingredient")
            .order_by("ingredient__name", "id")
        )

    def add(self, user, ingredient):
        """Add an ingredient to a user's inventory. Returns (item, created).

        Adding an ingredient the user already has returns the existing item
        instead of creating a second one.

        There is deliberately no "does it exist?" check first. The database's
        unique constraint decides, so two requests adding the same ingredient
        at the same moment still end up with exactly one row.
        """
        try:
            # Savepoint, so a rejected insert doesn't break the surrounding transaction.
            with transaction.atomic():
                return self.create(user=user, ingredient=ingredient), True
        except IntegrityError:
            existing = (
                self.select_related("ingredient")
                .filter(user=user, ingredient=ingredient)
                .first()
            )
            if existing is None:
                raise  # A different integrity problem, not a duplicate.
            return existing, False


class InventoryItem(models.Model):
    """One canonical Ingredient that one registered user has on hand."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # Inventory is private data, so it is removed along with the account.
        on_delete=models.CASCADE,
        related_name="inventory_items",
        # The (user, ingredient) unique constraint below already creates an
        # index that starts with user_id, which serves "WHERE user_id = ?"
        # lookups. A separate index would be redundant.
        db_index=False,
    )
    ingredient = models.ForeignKey(
        "ingredients.Ingredient",
        # Deleting a canonical ingredient removes it from users' inventories.
        # Deleting an inventory item never deletes the ingredient itself.
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = InventoryItemManager()

    class Meta:
        constraints = [
            # database-design.md: UNIQUE(user_id, ingredient_id)
            models.UniqueConstraint(
                fields=["user", "ingredient"], name="unique_inventory_user_ingredient"
            ),
        ]

    def __str__(self):
        return f"{self.ingredient} ({self.user})"

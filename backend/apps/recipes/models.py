"""
Recipe domain models (Issue #4).

Answers "What is this recipe, what ingredients does it require, how is it
prepared, and how is it classified?" It does NOT decide whether a user can
make a recipe; that belongs to the recommendations app.

Fields follow docs/database-design.md sections 9, 10, 15 and 22.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch


def validate_positive_quantity(value):
    """Quantities are optional, but when given they must be greater than zero."""
    if value is not None and value <= 0:
        raise ValidationError("Quantity must be greater than zero.")


class Tag(models.Model):
    """A standardized classification shared by recipes and user preferences.

    Examples: Korean [CUISINE], Vegan [DIET], Cheap [COST], Quick [OTHER].
    """

    class TagType(models.TextChoices):
        DIET = "DIET", "Diet"
        CUISINE = "CUISINE", "Cuisine"
        COST = "COST", "Cost"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=TagType.choices)

    class Meta:
        ordering = ["type", "name"]
        constraints = [
            # database-design.md: UNIQUE(name, type). Listing `type` first lets
            # the same index also serve "all tags of type X" lookups.
            models.UniqueConstraint(fields=["type", "name"], name="unique_tag_type_name"),
        ]

    def __str__(self):
        return f"{self.name} [{self.type}]"


class RecipeQuerySet(models.QuerySet):
    """Reusable query shapes that load related data up front (no N+1 queries)."""

    def with_list_relations(self):
        # The list response shows tags but not ingredients.
        return self.prefetch_related("tags")

    def with_detail_relations(self):
        # One query for tags, one for recipe ingredients joined to their
        # canonical Ingredient, regardless of how many there are.
        return self.prefetch_related(
            "tags",
            Prefetch(
                "recipe_ingredients",
                queryset=RecipeIngredient.objects.select_related("ingredient"),
            ),
        )


class Recipe(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # Deleting a user keeps their recipes (other users may have saved or
        # reviewed them). An empty owner also covers seed recipes; only admins
        # can edit a recipe with no owner.
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    preparation_time = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    cooking_time = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    # database-design.md "image_reference": the database stores only the
    # storage key. The file lives in whatever storage backend settings configure
    # (S3 in AWS), which also builds the URL, so no provider URL is hardcoded here.
    image = models.ImageField(upload_to="recipes/", blank=True)
    tags = models.ManyToManyField(Tag, related_name="recipes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RecipeQuerySet.as_manager()

    class Meta:
        # Stable order so pagination never skips or repeats recipes.
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """One canonical Ingredient used by one Recipe, plus recipe-specific details."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        # The (recipe, ingredient) unique constraint below already creates an
        # index that starts with recipe_id, so a separate one would be redundant.
        db_index=False,
    )
    ingredient = models.ForeignKey(
        "ingredients.Ingredient",
        # An Ingredient used by recipes can't be deleted out from under them.
        on_delete=models.PROTECT,
        related_name="recipe_ingredients",
    )
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[validate_positive_quantity],
    )
    unit = models.CharField(max_length=32, null=True, blank=True)
    is_optional = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        # database-design.md defines no position field, so ingredients come back
        # in the order they were added.
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["recipe", "ingredient"], name="unique_recipe_ingredient"),
        ]

    def __str__(self):
        return f"{self.ingredient} in {self.recipe}"

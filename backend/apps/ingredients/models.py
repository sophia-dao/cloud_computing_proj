
from django.db import models
from django.db.models.functions import Lower

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    allergens = models.ManyToManyField(
        "users.Allergen",
        blank=True,
        related_name="ingredients",
    )

    allergens_verified = models.BooleanField(
        default=False,
        help_text="Whether allergen information has been reviewed.",
    )

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_ingredient_name_case_insensitive",
            ),
        ]

    def __str__(self):
        return self.name

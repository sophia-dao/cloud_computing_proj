
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name

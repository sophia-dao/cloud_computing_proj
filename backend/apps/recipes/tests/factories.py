"""
Small helpers for building test data.

If the real User or Ingredient models have extra required fields, adjust
make_user / make_ingredient here; every test goes through these two functions.
"""

import itertools

from django.contrib.auth import get_user_model

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, Tag

_counter = itertools.count(1)


def make_user(is_admin=False):
    User = get_user_model()
    n = next(_counter)
    # USERNAME_FIELD exists on every Django user model, custom or not.
    return User.objects.create(**{User.USERNAME_FIELD: f"user{n}@example.com"}, is_staff=is_admin)


def make_ingredient(name):
    return Ingredient.objects.create(name=name)


def make_tag(name, type):
    return Tag.objects.create(name=name, type=type)


def make_recipe(name="Test Recipe", owner=None, ingredients=(), tags=()):
    """`ingredients` is a list of Ingredient objects, or (Ingredient, {field: value}) pairs."""
    recipe = Recipe.objects.create(name=name, owner=owner, instructions="Cook it.")
    for item in ingredients:
        ingredient, extra = item if isinstance(item, tuple) else (item, {})
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, **extra)
    recipe.tags.set(tags)
    return recipe

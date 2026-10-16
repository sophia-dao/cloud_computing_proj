"""
Small helpers for building test data.

If the real User or Ingredient models have extra required fields, adjust
make_user / make_ingredient here; every test goes through these functions.
"""

import itertools

from django.contrib.auth import get_user_model

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem

_counter = itertools.count(1)


def make_user():
    User = get_user_model()
    n = next(_counter)
    # USERNAME_FIELD exists on every Django user model, custom or not.
    return User.objects.create(**{User.USERNAME_FIELD: f"inventory-user{n}@example.com"})


def make_ingredient(name):
    return Ingredient.objects.create(name=name)


def add_item(user, ingredient):
    return InventoryItem.objects.create(user=user, ingredient=ingredient)

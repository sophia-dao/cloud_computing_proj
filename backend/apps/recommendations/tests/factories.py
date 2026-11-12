"""
Small helpers for building test data.

If the real models gain extra required fields, adjust the helpers here;
every test goes through these functions.
"""

import itertools

from django.contrib.auth import get_user_model

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.users.models import Allergen, User, UserAllergy, UserPreference

_counter = itertools.count(1)


def make_auth_user():
    AuthUser = get_user_model()
    n = next(_counter)
    return AuthUser.objects.create(**{AuthUser.USERNAME_FIELD: f"recommend-user{n}"})


def make_app_user(**fields):
    """A logged-in account: (Django auth user, application User)."""
    auth_user = make_auth_user()
    return auth_user, User.objects.create(auth_user=auth_user, **fields)


def make_ingredient(name, verified=True, allergens=()):
    ingredient = Ingredient.objects.create(name=name, allergens_verified=verified)
    ingredient.allergens.set(allergens)
    return ingredient


def make_ingredients(*names):
    return [make_ingredient(name) for name in names]


def make_tag(name, type):
    return Tag.objects.create(name=name, type=type)


def make_allergen(name):
    return Allergen.objects.create(name=name)


def make_recipe(name, required=(), optional=(), tags=()):
    recipe = Recipe.objects.create(name=name, instructions="Cook it.")
    for ingredient in required:
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient)
    for ingredient in optional:
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, is_optional=True)
    recipe.tags.set(tags)
    return recipe


def save_inventory(auth_user, *ingredients):
    for ingredient in ingredients:
        InventoryItem.objects.create(user=auth_user, ingredient=ingredient)


def save_preferences(app_user, *tags):
    for tag in tags:
        UserPreference.objects.create(user=app_user, tag=tag)


def save_allergies(app_user, *allergens):
    for allergen in allergens:
        UserAllergy.objects.create(user=app_user, allergen=allergen)


def ids(*objects):
    return [obj.id for obj in objects]

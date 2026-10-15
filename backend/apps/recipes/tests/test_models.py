from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, Tag

from .factories import make_ingredient, make_recipe, make_tag


class RecipeModelTests(TestCase):
    def test_recipe_can_be_stored_and_retrieved(self):
        recipe = Recipe.objects.create(
            name="Chicken Fried Rice",
            description="A simple chicken fried rice recipe.",
            instructions="Fry everything.",
            preparation_time=10,
            cooking_time=15,
        )
        fetched = Recipe.objects.get(pk=recipe.pk)
        self.assertEqual(fetched.name, "Chicken Fried Rice")
        self.assertEqual(fetched.description, "A simple chicken fried rice recipe.")
        self.assertEqual(fetched.instructions, "Fry everything.")
        self.assertEqual(fetched.preparation_time, 10)
        self.assertEqual(fetched.cooking_time, 15)
        self.assertIsNotNone(fetched.created_at)
        self.assertIsNotNone(fetched.updated_at)

    def test_image_is_stored_as_a_reference_not_binary(self):
        recipe = make_recipe()
        recipe.image = "recipes/fried-rice.jpg"
        recipe.save()
        recipe.refresh_from_db()
        # The database column holds only the storage key.
        self.assertEqual(recipe.image.name, "recipes/fried-rice.jpg")


class RecipeIngredientModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.chicken = make_ingredient("Chicken")
        cls.rice = make_ingredient("Rice")
        cls.egg = make_ingredient("Egg")
        cls.soy = make_ingredient("Soy Sauce")
        cls.green_onion = make_ingredient("Green Onion")

    def test_recipe_with_multiple_ingredients(self):
        recipe = make_recipe("Chicken Fried Rice", ingredients=[self.chicken, self.rice, self.egg, self.soy])
        stored = [ri.ingredient for ri in recipe.recipe_ingredients.all()]
        self.assertEqual(stored, [self.chicken, self.rice, self.egg, self.soy])

    def test_required_vs_optional_ingredients(self):
        recipe = make_recipe(
            ingredients=[self.chicken, self.rice, (self.green_onion, {"is_optional": True})]
        )
        flags = {ri.ingredient.name: ri.is_optional for ri in recipe.recipe_ingredients.all()}
        self.assertEqual(flags, {"Chicken": False, "Rice": False, "Green Onion": True})

    def test_references_canonical_ingredient_without_creating_one(self):
        before = Ingredient.objects.count()
        recipe = make_recipe(ingredients=[self.egg])
        ri = recipe.recipe_ingredients.get()
        self.assertEqual(ri.ingredient_id, self.egg.pk)
        self.assertEqual(Ingredient.objects.count(), before)
        self.assertEqual(Ingredient.objects.filter(name="Egg").count(), 1)

    def test_duplicate_recipe_ingredient_rejected_by_database(self):
        recipe = make_recipe("Chicken Fried Rice", ingredients=[self.egg])
        with self.assertRaises(IntegrityError), transaction.atomic():
            RecipeIngredient.objects.create(recipe=recipe, ingredient=self.egg)

    def test_same_ingredient_across_recipes_is_valid(self):
        recipe_a = make_recipe("Recipe A", ingredients=[self.egg])
        recipe_b = make_recipe("Recipe B", ingredients=[self.egg])
        self.assertEqual(recipe_a.recipe_ingredients.get().ingredient, self.egg)
        self.assertEqual(recipe_b.recipe_ingredients.get().ingredient, self.egg)

    def test_quantity_and_unit_are_stored(self):
        recipe = make_recipe(ingredients=[(self.chicken, {"quantity": Decimal("200"), "unit": "g"})])
        ri = recipe.recipe_ingredients.get()
        self.assertEqual(ri.quantity, Decimal("200"))
        self.assertEqual(ri.unit, "g")

    def test_quantity_must_be_positive(self):
        recipe = make_recipe()
        for bad in (Decimal("0"), Decimal("-2")):
            ri = RecipeIngredient(recipe=recipe, ingredient=self.egg, quantity=bad)
            with self.assertRaises(ValidationError):
                ri.full_clean()

    def test_quantity_and_unit_may_be_empty(self):
        recipe = make_recipe()
        ri = RecipeIngredient(recipe=recipe, ingredient=self.egg)
        ri.full_clean()  # no error

    def test_ingredients_have_deterministic_order(self):
        recipe = make_recipe(ingredients=[self.soy, self.chicken, self.egg])
        names = [ri.ingredient.name for ri in recipe.recipe_ingredients.all()]
        self.assertEqual(names, ["Soy Sauce", "Chicken", "Egg"])


class TagModelTests(TestCase):
    def test_tag_relationship(self):
        korean = make_tag("Korean", Tag.TagType.CUISINE)
        quick = make_tag("Quick", Tag.TagType.OTHER)
        recipe = make_recipe("Kimchi Fried Rice", tags=[korean, quick])
        self.assertEqual(set(recipe.tags.all()), {korean, quick})

    def test_documented_tag_types_supported(self):
        for tag_type in ["DIET", "CUISINE", "COST", "OTHER"]:
            Tag(name=f"Example {tag_type}", type=tag_type).full_clean()

    def test_invalid_tag_type_rejected(self):
        with self.assertRaises(ValidationError):
            Tag(name="Sparkly", type="MAGIC").full_clean()

    def test_duplicate_tag_rejected_by_database(self):
        make_tag("Korean", Tag.TagType.CUISINE)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Tag.objects.create(name="Korean", type=Tag.TagType.CUISINE)

    def test_same_name_allowed_under_different_types(self):
        make_tag("American", Tag.TagType.CUISINE)
        make_tag("American", Tag.TagType.OTHER)
        self.assertEqual(Tag.objects.filter(name="American").count(), 2)

    def test_recipe_cannot_get_same_tag_twice(self):
        korean = make_tag("Korean", Tag.TagType.CUISINE)
        recipe = make_recipe(tags=[korean])
        recipe.tags.add(korean)
        self.assertEqual(recipe.tags.count(), 1)

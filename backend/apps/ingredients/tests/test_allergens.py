from django.test import TestCase

from apps.ingredients.models import Ingredient
from apps.users.models import Allergen


class IngredientAllergenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.peanut = Allergen.objects.create(name="Peanut")
        cls.milk = Allergen.objects.create(name="Milk")
        cls.peanut_butter = Ingredient.objects.create(name="Peanut Butter")
        cls.rice = Ingredient.objects.create(name="Rice")

    def test_ingredient_has_no_allergens_by_default(self):
        self.assertFalse(self.rice.allergens.exists())

    def test_ingredient_can_have_several_allergens(self):
        self.peanut_butter.allergens.add(self.peanut, self.milk)

        self.assertEqual(
            set(self.peanut_butter.allergens.all()), {self.peanut, self.milk}
        )

    def test_allergen_lists_its_ingredients(self):
        self.peanut_butter.allergens.add(self.peanut)

        self.assertEqual(list(self.peanut.ingredients.all()), [self.peanut_butter])

    def test_adding_the_same_allergen_twice_keeps_one_link(self):
        self.peanut_butter.allergens.add(self.peanut)
        self.peanut_butter.allergens.add(self.peanut)

        self.assertEqual(self.peanut_butter.allergens.count(), 1)

    def test_ingredients_can_be_filtered_by_allergen(self):
        self.peanut_butter.allergens.add(self.peanut)

        self.assertEqual(
            list(Ingredient.objects.filter(allergens=self.peanut)),
            [self.peanut_butter],
        )

    def test_ingredient_api_response_is_unchanged(self):
        self.peanut_butter.allergens.add(self.peanut)

        response = self.client.get(f"/api/ingredients/{self.peanut_butter.id}/")

        self.assertEqual(
            response.json(),
            {"id": self.peanut_butter.id, "name": "Peanut Butter", "category": ""},
        )

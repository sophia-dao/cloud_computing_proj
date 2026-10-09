
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer


class IngredientModelTests(TestCase):
    def test_create_ingredient(self):
        ingredient = Ingredient.objects.create(
            name="Chicken Breast",
            category="Poultry",
        )
        self.assertIsNotNone(ingredient.pk)
        self.assertEqual(str(ingredient), "Chicken Breast")

    def test_optional_category(self):
        ingredient = Ingredient.objects.create(name="Rice")
        self.assertEqual(ingredient.category, "")

    
    def test_unique_name(self):
        Ingredient.objects.create(name="Chicken Breast")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.create(name="Chicken Breast")


    def test_case_insensitive_unique_name(self):
        Ingredient.objects.create(name="Chicken Breast")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.create(name="chicken breast")


    def test_uppercase_duplicate_name(self):
        Ingredient.objects.create(name="Chicken Breast")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.create(name="CHICKEN BREAST")

    def test_serialization(self):
        ingredient = Ingredient.objects.create(
            name="Chicken Breast", category="Poultry"
        )
        data = IngredientSerializer(ingredient).data
        self.assertEqual(
            dict(data),
            {
                "id": ingredient.id,
                "name": "Chicken Breast",
                "category": "Poultry",
            },
        )


class IngredientAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chicken = Ingredient.objects.create(
            name="Chicken Breast", category="Poultry"
        )
        Ingredient.objects.create(name="Ground Chicken")
        Ingredient.objects.create(name="White Rice")

    def test_list(self):
        response = self.client.get(reverse("ingredient-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

    def test_detail(self):
        response = self.client.get(
            reverse("ingredient-detail", args=[self.chicken.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.chicken.pk)

    def test_missing_detail(self):
        response = self.client.get(
            reverse("ingredient-detail", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_case_insensitive_partial_search(self):
        response = self.client.get(
            reverse("ingredient-list"), {"search": "CHICK"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_no_matches(self):
        response = self.client.get(
            reverse("ingredient-list"), {"search": "banana"}
        )
        self.assertEqual(response.data["count"], 0)

    def test_pagination(self):
        for i in range(30):
            Ingredient.objects.create(name=f"Test Ingredient {i:03d}")

        response = self.client.get(
            reverse("ingredient-list"), {"page_size": 10}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 33)
        self.assertIsNotNone(response.data["next"])

    def test_invalid_search(self):
        response = self.client.get(
            reverse("ingredient-list"), {"search": "x" * 256}
        )
        self.assertEqual(response.status_code, 400)

    def test_public_cannot_create(self):
        response = self.client.post(
            reverse("ingredient-list"),
            {"id": 999, "name": "Injected Ingredient"},
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            Ingredient.objects.filter(name="Injected Ingredient").exists()
        )

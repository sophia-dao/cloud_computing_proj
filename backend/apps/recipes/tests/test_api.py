from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.recipes.serializers import TagSerializer

from .factories import make_ingredient, make_recipe, make_tag, make_user

LIST_URL = "/api/recipes/"


def detail_url(recipe_id):
    return f"/api/recipes/{recipe_id}/"


# A guest's write attempt gets 401 or 403 depending on which authentication
# class the project configures (a Cognito token class gives 401). Both mean "rejected".
REJECTED_FOR_GUEST = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class RecipeReadAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.chicken = make_ingredient("Chicken Breast")
        cls.rice = make_ingredient("White Rice")
        cls.egg = make_ingredient("Egg")
        cls.soy = make_ingredient("Soy Sauce")
        cls.green_onion = make_ingredient("Green Onion")
        cls.korean = make_tag("Korean", Tag.TagType.CUISINE)
        cls.quick = make_tag("Quick", Tag.TagType.OTHER)
        cls.recipe = make_recipe(
            "Chicken Fried Rice",
            owner=cls.owner,
            ingredients=[
                (cls.chicken, {"quantity": 200, "unit": "g"}),
                (cls.rice, {"quantity": 2, "unit": "cups"}),
                (cls.egg, {"quantity": 2}),
                (cls.soy, {"quantity": 2, "unit": "tbsp"}),
                (cls.green_onion, {"quantity": 1, "unit": "stalk", "is_optional": True, "notes": "for garnish"}),
            ],
            tags=[cls.korean, cls.quick],
        )

    def test_guest_can_list_recipes(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_uses_small_representation(self):
        item = self.client.get(LIST_URL).data["results"][0]
        self.assertEqual(set(item), {"id", "name", "description", "image", "tags"})
        self.assertEqual(
            item["tags"],
            [
                {"id": self.korean.id, "name": "Korean", "type": "CUISINE"},
                {"id": self.quick.id, "name": "Quick", "type": "OTHER"},
            ],
        )

    def test_guest_can_view_recipe_detail(self):
        response = self.client.get(detail_url(self.recipe.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        for field in ["id", "owner", "name", "description", "preparation_time", "cooking_time",
                      "ingredients", "tags", "instructions", "image"]:
            self.assertIn(field, data)
        self.assertEqual(data["name"], "Chicken Fried Rice")
        self.assertEqual(data["instructions"], "Cook it.")
        self.assertEqual(data["owner"], {"id": self.owner.id})
        self.assertIsNone(data["image"])
        self.assertEqual({t["name"] for t in data["tags"]}, {"Korean", "Quick"})

    def test_detail_returns_all_ingredients_in_order(self):
        ingredients = self.client.get(detail_url(self.recipe.id)).data["ingredients"]
        names = [i["ingredient"]["name"] for i in ingredients]
        self.assertEqual(names, ["Chicken Breast", "White Rice", "Egg", "Soy Sauce", "Green Onion"])

    def test_detail_ingredient_fields(self):
        ingredients = self.client.get(detail_url(self.recipe.id)).data["ingredients"]
        self.assertEqual(
            ingredients[0],
            {
                "ingredient": {"id": self.chicken.id, "name": "Chicken Breast"},
                "quantity": 200,
                "unit": "g",
                "is_optional": False,
                "notes": None,
            },
        )
        egg = ingredients[2]
        self.assertIsNone(egg["unit"])
        green_onion = ingredients[4]
        self.assertTrue(green_onion["is_optional"])
        self.assertEqual(green_onion["notes"], "for garnish")

    def test_nonexistent_recipe_returns_404(self):
        response = self.client.get(detail_url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_image_url_comes_from_configured_storage(self):
        self.recipe.image = "recipes/fried-rice.jpg"
        self.recipe.save()
        image = self.client.get(detail_url(self.recipe.id)).data["image"]
        self.assertTrue(image.endswith("recipes/fried-rice.jpg"))


class RecipePaginationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(25):
            make_recipe(f"Recipe {i:02d}")

    def test_list_is_paginated(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_second_page_has_the_rest(self):
        response = self.client.get(LIST_URL, {"page": 2})
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNone(response.data["next"])

    def test_pages_do_not_overlap(self):
        page1 = {r["id"] for r in self.client.get(LIST_URL).data["results"]}
        page2 = {r["id"] for r in self.client.get(LIST_URL, {"page": 2}).data["results"]}
        self.assertFalse(page1 & page2)
        self.assertEqual(len(page1 | page2), 25)


class RecipeCreateAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user()
        cls.egg = make_ingredient("Egg")
        cls.rice = make_ingredient("White Rice")
        cls.korean = make_tag("Korean", Tag.TagType.CUISINE)
        cls.cheap = make_tag("Cheap", Tag.TagType.COST)

    def payload(self, **overrides):
        data = {
            "name": "Simple Egg Fried Rice",
            "description": "Quick fried rice.",
            "preparation_time": 10,
            "cooking_time": 15,
            "ingredients": [
                {"ingredient_id": self.egg.id, "quantity": 2, "unit": None, "is_optional": False, "notes": None},
                {"ingredient_id": self.rice.id, "quantity": 2, "unit": "cups", "is_optional": False, "notes": None},
            ],
            "tag_ids": [self.korean.id, self.cheap.id],
            "instructions": "Fry the rice, add the egg.",
        }
        data.update(overrides)
        return data

    def assert_nothing_created(self, ingredients_before):
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeIngredient.objects.count(), 0)
        self.assertEqual(Ingredient.objects.count(), ingredients_before)

    def test_guest_cannot_create(self):
        response = self.client.post(LIST_URL, self.payload(), format="json")
        self.assertIn(response.status_code, REJECTED_FOR_GUEST)
        self.assertEqual(Recipe.objects.count(), 0)

    def test_user_creates_recipe_and_becomes_owner(self):
        other = make_user()
        self.client.force_authenticate(self.user)
        # owner_id from the client must be ignored.
        response = self.client.post(LIST_URL, self.payload(owner_id=other.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get()
        self.assertEqual(recipe.owner, self.user)
        self.assertEqual(response.data["owner"], {"id": self.user.id})
        self.assertEqual([i["ingredient"]["name"] for i in response.data["ingredients"]], ["Egg", "White Rice"])
        self.assertEqual({t["id"] for t in response.data["tags"]}, {self.korean.id, self.cheap.id})

    def test_create_reuses_canonical_ingredients(self):
        before = Ingredient.objects.count()
        self.client.force_authenticate(self.user)
        self.client.post(LIST_URL, self.payload(), format="json")
        self.assertEqual(Ingredient.objects.count(), before)
        ids = set(RecipeIngredient.objects.values_list("ingredient_id", flat=True))
        self.assertEqual(ids, {self.egg.id, self.rice.id})

    def test_invalid_ingredient_id_rejected(self):
        before = Ingredient.objects.count()
        self.client.force_authenticate(self.user)
        bad = {"ingredient_id": 999999, "quantity": 2, "unit": "item"}
        response = self.client.post(LIST_URL, self.payload(ingredients=[bad]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ingredients", response.data)
        self.assert_nothing_created(before)

    def test_duplicate_ingredient_in_request_rejected(self):
        before = Ingredient.objects.count()
        self.client.force_authenticate(self.user)
        egg = {"ingredient_id": self.egg.id, "quantity": 1}
        response = self.client.post(LIST_URL, self.payload(ingredients=[egg, egg]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ingredients", response.data)
        self.assert_nothing_created(before)

    def test_zero_or_negative_quantity_rejected(self):
        self.client.force_authenticate(self.user)
        for bad in (0, -2):
            item = {"ingredient_id": self.egg.id, "quantity": bad}
            response = self.client.post(LIST_URL, self.payload(ingredients=[item]), format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad)
        self.assertEqual(Recipe.objects.count(), 0)

    def test_overlong_unit_rejected(self):
        self.client.force_authenticate(self.user)
        item = {"ingredient_id": self.egg.id, "quantity": 1, "unit": "x" * 33}
        response = self.client.post(LIST_URL, self.payload(ingredients=[item]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_unit_and_notes_stored_as_null(self):
        self.client.force_authenticate(self.user)
        item = {"ingredient_id": self.egg.id, "quantity": 1, "unit": "", "notes": ""}
        response = self.client.post(LIST_URL, self.payload(ingredients=[item]), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ri = RecipeIngredient.objects.get()
        self.assertIsNone(ri.unit)
        self.assertIsNone(ri.notes)

    def test_optional_flag_must_be_boolean(self):
        self.client.force_authenticate(self.user)
        item = {"ingredient_id": self.egg.id, "is_optional": "sometimes"}
        response = self.client.post(LIST_URL, self.payload(ingredients=[item]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_tag_id_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(LIST_URL, self.payload(tag_ids=[999999]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tag_ids", response.data)
        self.assertEqual(Recipe.objects.count(), 0)

    def test_missing_required_fields_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["name", "instructions", "ingredients"]:
            self.assertIn(field, response.data)

    def test_empty_ingredient_list_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(LIST_URL, self.payload(ingredients=[]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TagValidationTests(APITestCase):
    def test_tag_serializer_accepts_documented_type(self):
        serializer = TagSerializer(data={"name": "Vegan", "type": "DIET"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_tag_serializer_rejects_invalid_type(self):
        serializer = TagSerializer(data={"name": "Sparkly", "type": "MAGIC"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_tag_serializer_rejects_duplicate(self):
        make_tag("Korean", Tag.TagType.CUISINE)
        serializer = TagSerializer(data={"name": "Korean", "type": "CUISINE"})
        self.assertFalse(serializer.is_valid())


class RecipeModifyPermissionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.other_user = make_user()
        cls.admin = make_user(is_admin=True)
        cls.egg = make_ingredient("Egg")
        cls.rice = make_ingredient("White Rice")
        cls.korean = make_tag("Korean", Tag.TagType.CUISINE)

    def setUp(self):
        self.recipe = make_recipe("Egg Rice", owner=self.owner, ingredients=[self.egg], tags=[self.korean])

    def test_guest_cannot_delete(self):
        response = self.client.delete(detail_url(self.recipe.id))
        self.assertIn(response.status_code, REJECTED_FOR_GUEST)
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_guest_cannot_patch(self):
        response = self.client.patch(detail_url(self.recipe.id), {"name": "Hacked"}, format="json")
        self.assertIn(response.status_code, REJECTED_FOR_GUEST)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Egg Rice")

    def test_other_user_cannot_delete(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.delete(detail_url(self.recipe.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_other_user_cannot_patch(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.patch(detail_url(self.recipe.id), {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Egg Rice")

    def test_other_user_cannot_change_ingredients(self):
        self.client.force_authenticate(self.other_user)
        body = {"ingredients": [{"ingredient_id": self.rice.id}]}
        response = self.client.patch(detail_url(self.recipe.id), body, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.recipe.recipe_ingredients.get().ingredient, self.egg)

    def test_owner_can_patch_fields(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(detail_url(self.recipe.id), {"name": "Better Egg Rice"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Better Egg Rice")
        # Fields not sent are left alone.
        self.assertEqual(self.recipe.recipe_ingredients.get().ingredient, self.egg)
        self.assertEqual(list(self.recipe.tags.all()), [self.korean])

    def test_owner_can_replace_ingredients_and_tags(self):
        self.client.force_authenticate(self.owner)
        body = {
            "ingredients": [
                {"ingredient_id": self.rice.id, "quantity": 1, "unit": "cup"},
                {"ingredient_id": self.egg.id, "quantity": 3},
            ],
            "tag_ids": [],
        }
        response = self.client.patch(detail_url(self.recipe.id), body, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [i["ingredient"]["name"] for i in response.data["ingredients"]]
        self.assertEqual(names, ["White Rice", "Egg"])
        self.assertEqual(response.data["tags"], [])

    def test_owner_cannot_change_owner(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            detail_url(self.recipe.id), {"owner_id": self.other_user.id, "owner": self.other_user.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.owner, self.owner)

    def test_owner_can_delete(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(detail_url(self.recipe.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())
        # The canonical Ingredient survives.
        self.assertTrue(Ingredient.objects.filter(pk=self.egg.pk).exists())

    def test_admin_can_patch_any_recipe(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(detail_url(self.recipe.id), {"name": "Moderated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_any_recipe(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(detail_url(self.recipe.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_recipe_without_owner_only_editable_by_admin(self):
        seed = make_recipe("Seed Recipe", owner=None)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.delete(detail_url(seed.id)).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(detail_url(seed.id)).status_code, status.HTTP_204_NO_CONTENT)

    def test_patch_on_missing_recipe_returns_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(detail_url(999999), {"name": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecipeQueryEfficiencyTests(APITestCase):
    """The number of queries must not grow with the number of recipes, ingredients, or tags."""

    @classmethod
    def setUpTestData(cls):
        cls.ingredients = [make_ingredient(f"Ingredient {i}") for i in range(8)]
        cls.tags = [make_tag(f"Tag {i}", Tag.TagType.OTHER) for i in range(5)]

    def make_full_recipe(self, name, n_ingredients=3, n_tags=2):
        return make_recipe(name, ingredients=self.ingredients[:n_ingredients], tags=self.tags[:n_tags])

    def count_queries(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(ctx)

    def test_list_query_count_does_not_grow_with_recipes(self):
        for i in range(2):
            self.make_full_recipe(f"Small {i}")
        few = self.count_queries(LIST_URL)
        for i in range(10):
            self.make_full_recipe(f"More {i}", n_tags=5)
        many = self.count_queries(LIST_URL)
        self.assertEqual(few, many)

    def test_detail_query_count_does_not_grow_with_ingredients_or_tags(self):
        small = self.make_full_recipe("Small", n_ingredients=1, n_tags=1)
        big = self.make_full_recipe("Big", n_ingredients=8, n_tags=5)
        self.assertEqual(self.count_queries(detail_url(small.id)), self.count_queries(detail_url(big.id)))

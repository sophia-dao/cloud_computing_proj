from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem
from apps.recipes.models import Tag
from apps.users.models import User, UserAllergy, UserPreference

from .factories import (
    ids,
    make_allergen,
    make_app_user,
    make_auth_user,
    make_ingredient,
    make_ingredients,
    make_recipe,
    make_tag,
    save_allergies,
    save_inventory,
    save_preferences,
)

URL = "/api/recommendations/"

# A guest gets 401 or 403 depending on which authentication class the project
# configures (Basic or a Cognito token class gives 401). Both mean "rejected".
REJECTED_FOR_GUEST = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class RecommendationAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egg, cls.kimchi, cls.soy, cls.rice, cls.sesame, cls.chicken = make_ingredients(
            "Egg", "Kimchi", "Soy Sauce", "White Rice", "Sesame Seeds", "Chicken"
        )
        cls.fried_rice = make_recipe(
            "Kimchi Fried Rice",
            required=[cls.egg, cls.kimchi, cls.soy, cls.rice],
            optional=[cls.sesame],
        )
        cls.egg_soy = make_recipe("Egg with Soy Sauce", required=[cls.egg, cls.soy])

    def post(self, body, query=""):
        return self.client.post(URL + query, body, format="json")

    def recipe_names(self, response):
        return [result["recipe"]["name"] for result in response.data["results"]]


class GuestRecommendationTests(RecommendationAPITestCase):
    def test_guest_partial_match_response_shape(self):
        response = self.post({"ingredients": ids(self.egg, self.kimchi, self.soy), "match_mode": "PARTIAL_MATCH"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["match_mode"], "PARTIAL_MATCH")
        self.assertEqual(response.data["count"], 2)
        self.assertIsNone(response.data["next"])
        first, second = response.data["results"]
        self.assertEqual(first["recipe"], {"id": self.egg_soy.id, "name": "Egg with Soy Sauce", "image": None})
        self.assertEqual(first["match_score"], 1.0)
        self.assertEqual(second["recipe"]["name"], "Kimchi Fried Rice")
        self.assertEqual(second["match_score"], 0.75)
        self.assertEqual(
            second["available_ingredients"],
            [
                {"id": self.egg.id, "name": "Egg"},
                {"id": self.kimchi.id, "name": "Kimchi"},
                {"id": self.soy.id, "name": "Soy Sauce"},
            ],
        )
        self.assertEqual(second["missing_ingredients"], [{"id": self.rice.id, "name": "White Rice"}])
        self.assertEqual(second["optional_missing_ingredients"], [{"id": self.sesame.id, "name": "Sesame Seeds"}])

    def test_guest_available_only(self):
        response = self.post({"ingredients": ids(self.egg, self.kimchi, self.soy), "match_mode": "AVAILABLE_ONLY"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.recipe_names(response), ["Egg with Soy Sauce"])

    def test_guest_request_creates_no_saved_data(self):
        before = (InventoryItem.objects.count(), UserPreference.objects.count(), UserAllergy.objects.count())
        self.post({"ingredients": ids(self.egg), "match_mode": "PARTIAL_MATCH"})
        after = (InventoryItem.objects.count(), UserPreference.objects.count(), UserAllergy.objects.count())
        self.assertEqual(after, before)

    def test_duplicate_ids_do_not_change_scores(self):
        body = {"ingredients": ids(self.egg, self.egg, self.kimchi, self.kimchi, self.soy), "match_mode": "PARTIAL_MATCH"}
        self.assertEqual([r["match_score"] for r in self.post(body).data["results"]], [1.0, 0.75])

    def test_empty_ingredient_list_returns_empty_results(self):
        response = self.post({"ingredients": [], "match_mode": "PARTIAL_MATCH"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_tag_filter(self):
        korean = make_tag("Korean", Tag.TagType.CUISINE)
        self.fried_rice.tags.add(korean)
        response = self.post(
            {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH", "filters": {"tag_ids": [korean.id]}}
        )
        self.assertEqual(self.recipe_names(response), ["Kimchi Fried Rice"])

    def test_guest_allergen_filter(self):
        egg_allergen = make_allergen("Egg")
        self.egg.allergens.add(egg_allergen)
        make_recipe("Rice and soy", required=[self.rice, self.soy])
        response = self.post(
            {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH", "filters": {"allergen_ids": [egg_allergen.id]}}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.recipe_names(response), ["Rice and soy"])

    def test_unverified_ingredients_hidden_when_filtering_allergens(self):
        peanut = make_allergen("Peanut")
        mystery = make_ingredient("Mystery Sauce", verified=False)
        make_recipe("Egg with mystery sauce", required=[self.egg, mystery])
        body = {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH"}
        self.assertIn("Egg with mystery sauce", self.recipe_names(self.post(body)))
        body["filters"] = {"allergen_ids": [peanut.id]}
        self.assertNotIn("Egg with mystery sauce", self.recipe_names(self.post(body)))

    def test_same_request_gives_same_order(self):
        for i in range(5):
            make_recipe(f"Extra {i}", required=[self.egg, self.chicken])
        body = {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH"}
        orders = [[r["recipe"]["id"] for r in self.post(body).data["results"]] for _ in range(3)]
        self.assertEqual(orders[0], orders[1])
        self.assertEqual(orders[1], orders[2])


class ValidationTests(RecommendationAPITestCase):
    def assert_400(self, body, field):
        response = self.post(body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn(field, response.data)
        return response

    def test_invalid_mode(self):
        self.assert_400({"ingredients": ids(self.egg), "match_mode": "MAGIC_AI_MODE"}, "match_mode")

    def test_missing_mode(self):
        self.assert_400({"ingredients": ids(self.egg)}, "match_mode")

    def test_unknown_ingredient_id(self):
        before = Ingredient.objects.count()
        response = self.assert_400(
            {"ingredients": [self.egg.id, self.kimchi.id, 999999], "match_mode": "PARTIAL_MATCH"}, "ingredients"
        )
        self.assertIn("999999", str(response.data["ingredients"]))
        self.assertEqual(Ingredient.objects.count(), before)

    def test_malformed_ingredient_ids(self):
        for bad in ["abc", ["abc"], [0], [-1], [[1]], [None], {"id": 1}]:
            self.assert_400({"ingredients": bad, "match_mode": "PARTIAL_MATCH"}, "ingredients")

    def test_too_many_ids(self):
        self.assert_400({"ingredients": list(range(1, 502)), "match_mode": "PARTIAL_MATCH"}, "ingredients")

    def test_ingredients_required_without_saved_inventory(self):
        self.assert_400({"match_mode": "PARTIAL_MATCH"}, "ingredients")

    def test_unknown_tag_id(self):
        before = Tag.objects.count()
        response = self.assert_400(
            {"ingredients": ids(self.egg), "match_mode": "PARTIAL_MATCH", "filters": {"tag_ids": [999999]}}, "filters"
        )
        self.assertIn("tag_ids", response.data["filters"])
        self.assertEqual(Tag.objects.count(), before)

    def test_unknown_allergen_id(self):
        peanut = make_allergen("Peanut")
        response = self.assert_400(
            {"ingredients": ids(self.egg), "match_mode": "PARTIAL_MATCH", "filters": {"allergen_ids": [peanut.id, 999999]}},
            "filters",
        )
        self.assertIn("999999", str(response.data["filters"]["allergen_ids"]))

    def test_unknown_fields_rejected(self):
        self.assert_400({"ingredients": ids(self.egg), "match_mode": "PARTIAL_MATCH", "user_id": 5}, "user_id")

    def test_alternate_field_names_get_a_hint(self):
        response = self.assert_400({"ingredient_ids": ids(self.egg), "mode": "PARTIAL_MATCH"}, "ingredient_ids")
        self.assertIn("ingredients", str(response.data["ingredient_ids"]))
        self.assertIn("match_mode", str(response.data["mode"]))

    def test_unknown_filter_field_rejected(self):
        response = self.assert_400(
            {"ingredients": ids(self.egg), "match_mode": "PARTIAL_MATCH", "filters": {"cuisine": "korean"}}, "filters"
        )
        self.assertIn("cuisine", response.data["filters"])

    def test_both_ingredient_sources_rejected(self):
        self.client.force_authenticate(make_auth_user())
        self.assert_400(
            {"ingredients": ids(self.egg), "use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"}, "ingredients"
        )


class SavedInventoryTests(RecommendationAPITestCase):
    def test_guest_cannot_use_saved_inventory(self):
        response = self.post({"use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"})
        self.assertIn(response.status_code, REJECTED_FOR_GUEST)

    def test_uses_only_the_logged_in_users_inventory(self):
        user_a, user_b = make_auth_user(), make_auth_user()
        save_inventory(user_a, self.egg, self.soy)
        save_inventory(user_b, self.kimchi, self.rice)
        self.client.force_authenticate(user_a)
        response = self.post({"use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fried_rice = next(r for r in response.data["results"] if r["recipe"]["name"] == "Kimchi Fried Rice")
        self.assertEqual([i["name"] for i in fried_rice["available_ingredients"]], ["Egg", "Soy Sauce"])
        self.assertEqual([i["name"] for i in fried_rice["missing_ingredients"]], ["Kimchi", "White Rice"])

    def test_works_without_an_application_user_row(self):
        auth_user = make_auth_user()
        save_inventory(auth_user, self.egg, self.soy)
        self.client.force_authenticate(auth_user)
        response = self.post({"use_saved_inventory": True, "match_mode": "AVAILABLE_ONLY"})
        self.assertEqual(self.recipe_names(response), ["Egg with Soy Sauce"])

    def test_empty_saved_inventory_returns_empty_results(self):
        self.client.force_authenticate(make_auth_user())
        response = self.post({"use_saved_inventory": True, "match_mode": "AVAILABLE_ONLY"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_logged_in_user_can_still_send_ingredients_directly(self):
        user = make_auth_user()
        save_inventory(user, self.chicken)
        self.client.force_authenticate(user)
        response = self.post(
            {"ingredients": ids(self.egg, self.soy), "use_saved_inventory": False, "match_mode": "AVAILABLE_ONLY"}
        )
        self.assertEqual(self.recipe_names(response), ["Egg with Soy Sauce"])
        # The temporary search leaves the saved inventory untouched.
        saved = InventoryItem.objects.filter(user=user).values_list("ingredient_id", flat=True)
        self.assertEqual(list(saved), [self.chicken.id])


class SavedAllergyTests(RecommendationAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.egg_allergen = make_allergen("Egg")
        cls.soy_allergen = make_allergen("Soy")
        cls.egg.allergens.add(cls.egg_allergen)
        cls.soy.allergens.add(cls.soy_allergen)
        cls.rice_dish = make_recipe("Plain Rice", required=[cls.rice])

    def body(self, **extra):
        return {"ingredients": ids(self.egg, self.soy, self.rice), "match_mode": "PARTIAL_MATCH", **extra}

    def test_saved_allergies_always_applied(self):
        auth_user, app_user = make_app_user()
        save_allergies(app_user, self.egg_allergen)
        self.client.force_authenticate(auth_user)
        self.assertEqual(self.recipe_names(self.post(self.body())), ["Plain Rice"])

    def test_saved_and_request_allergies_combine(self):
        soy_free_egg = make_recipe("Boiled Egg", required=[self.egg])
        auth_user, app_user = make_app_user()
        save_allergies(app_user, self.soy_allergen)
        self.client.force_authenticate(auth_user)
        self.assertIn(soy_free_egg.name, self.recipe_names(self.post(self.body())))
        names = self.recipe_names(self.post(self.body(filters={"allergen_ids": [self.egg_allergen.id]})))
        self.assertEqual(names, ["Plain Rice"])

    def test_other_users_allergies_not_applied(self):
        auth_user, _ = make_app_user()
        _, someone_else = make_app_user()
        save_allergies(someone_else, self.egg_allergen)
        self.client.force_authenticate(auth_user)
        self.assertIn("Egg with Soy Sauce", self.recipe_names(self.post(self.body())))


class SavedPreferenceTests(RecommendationAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.korean = make_tag("Korean", Tag.TagType.CUISINE)
        cls.cheap = make_tag("Cheap", Tag.TagType.COST)
        cls.fried_rice.tags.add(cls.korean, cls.cheap)

    def body(self):
        return {"ingredients": ids(self.egg, self.kimchi, self.soy), "match_mode": "PARTIAL_MATCH"}

    def test_guest_order_is_by_ingredient_match(self):
        self.assertEqual(self.recipe_names(self.post(self.body())), ["Egg with Soy Sauce", "Kimchi Fried Rice"])

    def test_saved_cuisine_preference_moves_recipe_up(self):
        auth_user, app_user = make_app_user()
        save_preferences(app_user, self.korean)
        self.client.force_authenticate(auth_user)
        response = self.post(self.body())
        self.assertEqual(self.recipe_names(response), ["Kimchi Fried Rice", "Egg with Soy Sauce"])
        # Ranking only: scores and ingredient lists are unchanged.
        self.assertEqual([r["match_score"] for r in response.data["results"]], [0.75, 1.0])

    def test_cost_preference_does_not_affect_ranking(self):
        auth_user, app_user = make_app_user()
        save_preferences(app_user, self.cheap)
        self.client.force_authenticate(auth_user)
        self.assertEqual(self.recipe_names(self.post(self.body())), ["Egg with Soy Sauce", "Kimchi Fried Rice"])

    def test_other_users_preferences_not_used(self):
        auth_user, _ = make_app_user()
        _, someone_else = make_app_user()
        save_preferences(someone_else, self.korean)
        self.client.force_authenticate(auth_user)
        self.assertEqual(self.recipe_names(self.post(self.body())), ["Egg with Soy Sauce", "Kimchi Fried Rice"])

    def test_inactive_accounts_get_no_personalization(self):
        auth_user, app_user = make_app_user(account_status=User.AccountStatus.SUSPENDED)
        save_preferences(app_user, self.korean)
        self.client.force_authenticate(auth_user)
        self.assertEqual(self.recipe_names(self.post(self.body())), ["Egg with Soy Sauce", "Kimchi Fried Rice"])


class PaginationTests(RecommendationAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(25):
            make_recipe(f"Bulk {i:02d}", required=[cls.egg, cls.chicken])

    def test_results_are_paginated_and_stable(self):
        body = {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH"}
        page1 = self.post(body)
        page2 = self.post(body, "?page=2")
        self.assertEqual(page1.data["count"], 27)
        self.assertEqual(len(page1.data["results"]), 20)
        self.assertIsNotNone(page1.data["next"])
        self.assertEqual(len(page2.data["results"]), 7)
        self.assertIsNone(page2.data["next"])
        first_ids = {r["recipe"]["id"] for r in page1.data["results"]}
        second_ids = {r["recipe"]["id"] for r in page2.data["results"]}
        self.assertFalse(first_ids & second_ids)
        scores = [r["match_score"] for r in page1.data["results"] + page2.data["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_page_size_param(self):
        body = {"ingredients": ids(self.egg, self.soy), "match_mode": "PARTIAL_MATCH"}
        self.assertEqual(len(self.post(body, "?page_size=6").data["results"]), 6)


class APIQueryEfficiencyTests(RecommendationAPITestCase):
    def count_queries(self, body):
        with CaptureQueriesContext(connection) as ctx:
            response = self.post(body)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(ctx)

    def test_query_count_does_not_grow_with_recipes(self):
        auth_user, app_user = make_app_user()
        korean = make_tag("Korean", Tag.TagType.CUISINE)
        save_preferences(app_user, korean)
        save_allergies(app_user, make_allergen("Peanut"))
        save_inventory(auth_user, self.egg, self.soy, self.kimchi)
        self.client.force_authenticate(auth_user)
        body = {"use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"}
        small = self.count_queries(body)
        for i in range(15):
            recipe = make_recipe(f"More {i}", required=[self.egg, self.rice, self.chicken], optional=[self.sesame])
            if i % 2:
                recipe.tags.add(korean)
        self.assertEqual(small, self.count_queries(body))

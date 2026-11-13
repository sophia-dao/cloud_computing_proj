"""
Cross-module permission tests with real Cognito-style bearer tokens (Issue #68).

Unlike the per-app tests, which log users in with force_authenticate, every
request here goes through the actual authentication class, the way the React
app's requests do. Tokens come from the fake User Pool in apps/users/testing.py.
"""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.users.models import Allergen, User, UserAllergy, UserPreference
from apps.users.testing import CognitoTestMixin

ALICE = "sub-alice"
BOB = "sub-bob"


class PermissionTestCase(CognitoTestMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egg = Ingredient.objects.create(name="Egg", allergens_verified=True)
        cls.rice = Ingredient.objects.create(name="White Rice", allergens_verified=True)
        cls.vegan = Tag.objects.create(name="Vegan", type=Tag.TagType.DIET)
        cls.korean = Tag.objects.create(name="Korean", type=Tag.TagType.CUISINE)
        cls.peanut = Allergen.objects.create(name="Peanut")
        cls.public_recipe = Recipe.objects.create(name="Egg Rice", instructions="Cook.")
        RecipeIngredient.objects.create(recipe=cls.public_recipe, ingredient=cls.egg)

    def as_user(self, sub, method, url, data=None):
        call = getattr(self.client, method)
        return call(url, data, format="json", **self.bearer(self.pool.token(sub)))

    def app_user(self, sub):
        return User.objects.select_related("auth_user").get(cognito_subject=sub)

    def recipe_payload(self, name="Alice's Rice"):
        return {
            "name": name,
            "instructions": "Cook the rice.",
            "ingredients": [{"ingredient_id": self.rice.pk}],
        }


class GuestAccessTests(PermissionTestCase):
    def test_public_endpoints_work_without_a_token(self):
        for url in [
            "/api/recipes/",
            f"/api/recipes/{self.public_recipe.pk}/",
            "/api/tags/",
            "/api/ingredients/",
            "/api/users/allergens/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

        response = self.client.post(
            "/api/recommendations/",
            {"ingredients": [self.egg.pk], "match_mode": "PARTIAL_MATCH"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoints_need_a_token(self):
        recipe_url = f"/api/recipes/{self.public_recipe.pk}/"
        for method, url, data in [
            ("get", "/api/auth/me/", None),
            ("get", "/api/users/me/", None),
            ("patch", "/api/users/me/", {"display_name": "Guest"}),
            ("get", "/api/users/me/preferences/", None),
            ("put", "/api/users/me/preferences/", {"tag_ids": [self.vegan.pk]}),
            ("get", "/api/users/me/allergies/", None),
            ("put", "/api/users/me/allergies/", {"allergen_ids": [self.peanut.pk]}),
            ("get", "/api/inventory/", None),
            ("post", "/api/inventory/", {"ingredient_id": self.egg.pk}),
            ("post", "/api/recipes/", self.recipe_payload()),
            ("patch", recipe_url, {"name": "Hijacked"}),
            ("delete", recipe_url, None),
            (
                "post",
                "/api/recommendations/",
                {"use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"},
            ),
        ]:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.public_recipe.refresh_from_db()
        self.assertEqual(self.public_recipe.name, "Egg Rice")

    def test_bad_token_on_a_public_endpoint_is_401_not_guest(self):
        # The frontend refreshes the token and retries on 401, then falls back
        # to a guest request, so a bad token must not be silently ignored.
        with self.assertLogs("apps.users", level="INFO"):
            response = self.client.get(
                "/api/recipes/", **self.bearer(self.pool.token(client_id="other-client"))
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signed_in_users_can_still_browse(self):
        self.sign_in_as(ALICE)
        self.assertEqual(self.client.get("/api/recipes/").status_code, status.HTTP_200_OK)


class InventoryOwnershipTests(PermissionTestCase):
    def test_each_user_sees_only_their_own_inventory(self):
        self.assertEqual(self.as_user(ALICE, "post", "/api/inventory/", {"ingredient_id": self.egg.pk}).status_code, 201)
        self.assertEqual(self.as_user(BOB, "post", "/api/inventory/", {"ingredient_id": self.rice.pk}).status_code, 201)

        alice_items = self.as_user(ALICE, "get", "/api/inventory/").data["results"]
        bob_items = self.as_user(BOB, "get", "/api/inventory/").data["results"]
        self.assertEqual([item["ingredient"]["id"] for item in alice_items], [self.egg.pk])
        self.assertEqual([item["ingredient"]["id"] for item in bob_items], [self.rice.pk])

    def test_owner_comes_from_the_token_not_the_request_body(self):
        self.as_user(BOB, "get", "/api/auth/me/")
        bob = self.app_user(BOB)
        self.as_user(
            ALICE,
            "post",
            "/api/inventory/",
            {"ingredient_id": self.egg.pk, "user": bob.auth_user.pk, "user_id": bob.auth_user.pk},
        )
        item = InventoryItem.objects.get()
        self.assertEqual(item.user, self.app_user(ALICE).auth_user)

    def test_cannot_delete_someone_elses_item(self):
        item_id = self.as_user(ALICE, "post", "/api/inventory/", {"ingredient_id": self.egg.pk}).data["id"]

        response = self.as_user(BOB, "delete", f"/api/inventory/{item_id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(InventoryItem.objects.filter(pk=item_id).exists())
        self.assertEqual(
            self.as_user(ALICE, "delete", f"/api/inventory/{item_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_saved_inventory_recommendations_use_the_callers_inventory(self):
        self.as_user(BOB, "post", "/api/inventory/", {"ingredient_id": self.egg.pk})
        response = self.as_user(
            ALICE,
            "post",
            "/api/recommendations/",
            {"use_saved_inventory": True, "match_mode": "PARTIAL_MATCH"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


class PreferenceOwnershipTests(PermissionTestCase):
    def test_preferences_and_allergies_are_per_user(self):
        self.as_user(ALICE, "put", "/api/users/me/preferences/", {"tag_ids": [self.vegan.pk]})
        self.as_user(ALICE, "put", "/api/users/me/allergies/", {"allergen_ids": [self.peanut.pk]})
        self.as_user(BOB, "put", "/api/users/me/preferences/", {"tag_ids": [self.korean.pk]})

        alice_prefs = self.as_user(ALICE, "get", "/api/users/me/preferences/").data["preferences"]
        bob_prefs = self.as_user(BOB, "get", "/api/users/me/preferences/").data["preferences"]
        self.assertEqual([tag["id"] for tag in alice_prefs], [self.vegan.pk])
        self.assertEqual([tag["id"] for tag in bob_prefs], [self.korean.pk])
        self.assertEqual(self.as_user(BOB, "get", "/api/users/me/allergies/").data["allergies"], [])

        alice = self.app_user(ALICE)
        self.assertEqual(UserPreference.objects.filter(user=alice).count(), 1)
        self.assertEqual(UserAllergy.objects.filter(user=alice).count(), 1)


class RecipeOwnershipTests(PermissionTestCase):
    def create_as_alice(self):
        response = self.as_user(ALICE, "post", "/api/recipes/", self.recipe_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Recipe.objects.get(pk=response.data["id"])

    def test_submitted_recipe_is_owned_by_the_signed_in_user(self):
        self.as_user(BOB, "get", "/api/auth/me/")
        payload = {**self.recipe_payload(), "owner": self.app_user(BOB).auth_user.pk}
        response = self.as_user(ALICE, "post", "/api/recipes/", payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(pk=response.data["id"])
        self.assertEqual(recipe.owner, self.app_user(ALICE).auth_user)

    def test_only_the_owner_can_edit_or_delete(self):
        recipe = self.create_as_alice()
        url = f"/api/recipes/{recipe.pk}/"

        self.assertEqual(self.as_user(BOB, "patch", url, {"name": "Bob's now"}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.as_user(BOB, "delete", url).status_code, status.HTTP_403_FORBIDDEN)
        recipe.refresh_from_db()
        self.assertEqual(recipe.name, "Alice's Rice")

        self.assertEqual(self.as_user(ALICE, "patch", url, {"name": "Alice's Best Rice"}).status_code, status.HTTP_200_OK)
        self.assertEqual(self.as_user(ALICE, "delete", url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=recipe.pk).exists())

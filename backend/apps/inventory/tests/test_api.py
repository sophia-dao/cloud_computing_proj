from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem

from .factories import add_item, make_ingredient, make_user

LIST_URL = "/api/inventory/"


def item_url(item_id):
    return f"/api/inventory/{item_id}/"


# A guest gets 401 or 403 depending on which authentication class the project
# configures (a Cognito token class gives 401). Both mean "rejected".
REJECTED_FOR_GUEST = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class InventoryTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = make_user()
        cls.user_b = make_user()
        cls.egg = make_ingredient("Egg")
        cls.rice = make_ingredient("Rice")
        cls.chicken = make_ingredient("Chicken")

    def names_in(self, response):
        return [item["ingredient"]["name"] for item in response.data["results"]]


class RetrieveInventoryTests(InventoryTestCase):
    def test_user_sees_only_their_own_inventory(self):
        add_item(self.user_a, self.egg)
        add_item(self.user_a, self.rice)
        add_item(self.user_b, self.chicken)
        self.client.force_authenticate(self.user_a)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.names_in(response), ["Egg", "Rice"])

    def test_response_shape_matches_api_design(self):
        item = add_item(self.user_a, self.egg)
        self.client.force_authenticate(self.user_a)
        response = self.client.get(LIST_URL)
        self.assertEqual(
            response.data,
            {"results": [{"id": item.id, "ingredient": {"id": self.egg.id, "name": "Egg"}}]},
        )

    def test_empty_inventory_returns_empty_results(self):
        self.client.force_authenticate(self.user_a)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"results": []})

    def test_user_id_query_param_cannot_read_another_inventory(self):
        add_item(self.user_b, self.chicken)
        self.client.force_authenticate(self.user_a)
        response = self.client.get(LIST_URL, {"user_id": self.user_b.id})
        self.assertEqual(response.data, {"results": []})


class AddIngredientTests(InventoryTestCase):
    def test_add_ingredient(self):
        self.client.force_authenticate(self.user_a)
        response = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = InventoryItem.objects.get()
        self.assertEqual(item.user, self.user_a)
        self.assertEqual(item.ingredient, self.egg)
        self.assertEqual(response.data, {"id": item.id, "ingredient": {"id": self.egg.id, "name": "Egg"}})
        self.assertEqual(self.names_in(self.client.get(LIST_URL)), ["Egg"])

    def test_add_references_canonical_ingredient_without_creating_one(self):
        before = Ingredient.objects.count()
        self.client.force_authenticate(self.user_a)
        self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        self.assertEqual(Ingredient.objects.count(), before)
        self.assertEqual(InventoryItem.objects.get().ingredient_id, self.egg.id)

    def test_client_cannot_choose_owner(self):
        self.client.force_authenticate(self.user_a)
        response = self.client.post(
            LIST_URL, {"ingredient_id": self.egg.id, "user_id": self.user_b.id, "user": self.user_b.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.get().user, self.user_a)
        self.assertFalse(InventoryItem.objects.filter(user=self.user_b).exists())

    def test_duplicate_add_returns_existing_item(self):
        self.client.force_authenticate(self.user_a)
        first = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        second = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(InventoryItem.objects.filter(user=self.user_a, ingredient=self.egg).count(), 1)

    def test_same_ingredient_for_different_users(self):
        for user in (self.user_a, self.user_b):
            self.client.force_authenticate(user)
            response = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.filter(ingredient=self.egg).count(), 2)

    def test_invalid_ingredient_id_rejected(self):
        before = Ingredient.objects.count()
        self.client.force_authenticate(self.user_a)
        response = self.client.post(LIST_URL, {"ingredient_id": 999999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ingredient_id", response.data)
        self.assertFalse(InventoryItem.objects.exists())
        self.assertEqual(Ingredient.objects.count(), before)

    def test_missing_or_malformed_ingredient_id_rejected(self):
        self.client.force_authenticate(self.user_a)
        for body in ({}, {"ingredient_id": None}, {"ingredient_id": "egg"}):
            response = self.client.post(LIST_URL, body, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, body)
        self.assertFalse(InventoryItem.objects.exists())


class RemoveIngredientTests(InventoryTestCase):
    def test_owner_can_remove_item(self):
        item = add_item(self.user_a, self.egg)
        self.client.force_authenticate(self.user_a)
        response = self.client.delete(item_url(item.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InventoryItem.objects.filter(pk=item.pk).exists())
        # The canonical Ingredient survives.
        self.assertTrue(Ingredient.objects.filter(pk=self.egg.pk).exists())

    def test_remove_nonexistent_item_returns_404(self):
        self.client.force_authenticate(self.user_a)
        self.assertEqual(self.client.delete(item_url(999999)).status_code, status.HTTP_404_NOT_FOUND)

    def test_full_flow(self):
        """GET -> add -> GET -> remove -> GET, as in the issue's manual test."""
        self.client.force_authenticate(self.user_a)
        self.assertEqual(self.names_in(self.client.get(LIST_URL)), [])
        added = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        self.assertEqual(self.names_in(self.client.get(LIST_URL)), ["Egg"])
        self.client.delete(item_url(added.data["id"]))
        self.assertEqual(self.names_in(self.client.get(LIST_URL)), [])


class GuestAccessTests(InventoryTestCase):
    def test_guest_cannot_list(self):
        self.assertIn(self.client.get(LIST_URL).status_code, REJECTED_FOR_GUEST)

    def test_guest_cannot_add(self):
        response = self.client.post(LIST_URL, {"ingredient_id": self.egg.id}, format="json")
        self.assertIn(response.status_code, REJECTED_FOR_GUEST)
        self.assertFalse(InventoryItem.objects.exists())

    def test_guest_cannot_delete(self):
        item = add_item(self.user_a, self.egg)
        self.assertIn(self.client.delete(item_url(item.id)).status_code, REJECTED_FOR_GUEST)
        self.assertTrue(InventoryItem.objects.filter(pk=item.pk).exists())


class CrossUserAccessTests(InventoryTestCase):
    def setUp(self):
        self.item_a = add_item(self.user_a, self.egg)
        self.client.force_authenticate(self.user_b)

    def test_other_users_items_not_in_list(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.data, {"results": []})

    def test_cannot_retrieve_other_users_item(self):
        response = self.client.get(item_url(self.item_a.id))
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(b"Egg", response.content)

    def test_cannot_delete_other_users_item(self):
        response = self.client.delete(item_url(self.item_a.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(InventoryItem.objects.filter(pk=self.item_a.pk).exists())

    def test_cannot_update_other_users_item(self):
        response = self.client.patch(item_url(self.item_a.id), {"ingredient_id": self.rice.id}, format="json")
        self.assertIn(response.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED))
        self.item_a.refresh_from_db()
        self.assertEqual(self.item_a.ingredient, self.egg)
        self.assertEqual(self.item_a.user, self.user_a)

    def test_update_not_supported_even_for_owner(self):
        # database-design.md defines no editable inventory fields, so there is no PATCH.
        self.client.force_authenticate(self.user_a)
        response = self.client.patch(item_url(self.item_a.id), {"ingredient_id": self.rice.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.item_a.refresh_from_db()
        self.assertEqual(self.item_a.ingredient, self.egg)


class InventoryQueryEfficiencyTests(InventoryTestCase):
    """The number of queries must not grow with the number of inventory items."""

    def count_list_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(ctx)

    def test_list_query_count_does_not_grow_with_items(self):
        self.client.force_authenticate(self.user_a)
        add_item(self.user_a, self.egg)
        one_item = self.count_list_queries()
        for name in ["Soy Sauce", "Kimchi", "Garlic", "Green Onion"]:
            add_item(self.user_a, make_ingredient(name))
        add_item(self.user_a, self.rice)
        add_item(self.user_a, self.chicken)
        self.assertEqual(len(self.client.get(LIST_URL).data["results"]), 7)
        self.assertEqual(one_item, self.count_list_queries())

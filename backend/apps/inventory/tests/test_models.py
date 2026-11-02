from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.ingredients.models import Ingredient
from apps.inventory.models import InventoryItem

from .factories import add_item, make_ingredient, make_user


class InventoryItemModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = make_user()
        cls.user_b = make_user()
        cls.egg = make_ingredient("Egg")
        cls.rice = make_ingredient("Rice")

    def test_item_references_canonical_ingredient(self):
        before = Ingredient.objects.count()
        item = add_item(self.user_a, self.egg)
        item.refresh_from_db()
        self.assertEqual(item.ingredient_id, self.egg.id)
        self.assertEqual(Ingredient.objects.count(), before)
        self.assertEqual(Ingredient.objects.filter(name="Egg").count(), 1)

    def test_timestamps_are_set(self):
        item = add_item(self.user_a, self.egg)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)

    def test_duplicate_rejected_by_database(self):
        add_item(self.user_a, self.egg)
        with self.assertRaises(IntegrityError), transaction.atomic():
            InventoryItem.objects.create(user=self.user_a, ingredient=self.egg)

    def test_same_ingredient_for_different_users_is_valid(self):
        add_item(self.user_a, self.egg)
        add_item(self.user_b, self.egg)
        self.assertEqual(InventoryItem.objects.filter(ingredient=self.egg).count(), 2)

    def test_add_creates_then_returns_existing(self):
        first, created = InventoryItem.objects.add(user=self.user_a, ingredient=self.egg)
        self.assertTrue(created)
        second, created_again = InventoryItem.objects.add(user=self.user_a, ingredient=self.egg)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(InventoryItem.objects.filter(user=self.user_a).count(), 1)

    def test_rejected_duplicate_leaves_transaction_usable(self):
        InventoryItem.objects.add(user=self.user_a, ingredient=self.egg)
        InventoryItem.objects.add(user=self.user_a, ingredient=self.egg)
        # Further writes in the same transaction still work after the rejected insert.
        _, created = InventoryItem.objects.add(user=self.user_a, ingredient=self.rice)
        self.assertTrue(created)

    def test_for_user_returns_only_that_users_items_alphabetically(self):
        add_item(self.user_a, self.rice)
        add_item(self.user_a, self.egg)
        add_item(self.user_b, self.egg)
        names = [item.ingredient.name for item in InventoryItem.objects.for_user(self.user_a)]
        self.assertEqual(names, ["Egg", "Rice"])

    def test_deleting_item_keeps_ingredient(self):
        item = add_item(self.user_a, self.egg)
        item.delete()
        self.assertTrue(Ingredient.objects.filter(pk=self.egg.pk).exists())

    def test_deleting_user_removes_only_their_inventory(self):
        doomed = make_user()
        add_item(doomed, self.egg)
        add_item(self.user_b, self.egg)
        get_user_model().objects.filter(pk=doomed.pk).delete()
        self.assertFalse(InventoryItem.objects.filter(user_id=doomed.pk).exists())
        self.assertTrue(InventoryItem.objects.filter(user=self.user_b, ingredient=self.egg).exists())
        self.assertTrue(Ingredient.objects.filter(pk=self.egg.pk).exists())

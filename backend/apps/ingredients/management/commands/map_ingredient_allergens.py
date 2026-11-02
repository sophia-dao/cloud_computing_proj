
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.ingredients.models import Ingredient
from apps.users.models import Allergen



# Confirmed or strongly identifiable mappings from
# the current ingredient names.
# Product-dependent ingredients require separate review.

INGREDIENT_ALLERGEN_MAP = {
    "almonds": ["Tree Nuts"],
    "flaked almonds": ["Tree Nuts"],
    "ground almonds": ["Tree Nuts"],

    "butter": ["Milk"],
    "melted butter": ["Milk"],
    "salted butter": ["Milk"],
    "unsalted butter": ["Milk"],
    "milk": ["Milk"],
    "mozzarella": ["Milk"],
    "dulce de leche": ["Milk"],
    "queso fresco": ["Milk"],
    "ice cream": ["Milk"],

    "egg": ["Egg"],
    "eggs": ["Egg"],
    "egg yolks": ["Egg"],
    "free-range eggs, beaten": ["Egg"],

    "peanut butter": ["Peanut"],

    "semolina": ["Wheat"],
    "all purpose flour": ["Wheat"],
    "plain flour": ["Wheat"],
    "self-raising flour": ["Wheat"],

    "soy sauce": ["Soy"],

    "fish fillet": ["Fish"],
    "fish sauce": ["Fish"],

    "raw tiger prawns": ["Crustacean Shellfish"],
}

def detect_allergens(name):
    return INGREDIENT_ALLERGEN_MAP.get(
        name.strip().casefold(),
        [],
    )


class Command(BaseCommand):
    help = "Map known ingredient names to allergens."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview mappings without modifying the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        mapped_ingredients = 0
        added_relationships = 0
        unmatched = []

        with transaction.atomic():
            for ingredient in Ingredient.objects.all().iterator():
                detected = detect_allergens(ingredient.name)

                if not detected:
                    unmatched.append(ingredient.name)
                    continue

                mapped_ingredients += 1

                self.stdout.write(
                    f"{ingredient.name}: {', '.join(detected)}"
                )

                if dry_run:
                    continue

                for allergen_name in detected:
                    allergen, _ = Allergen.objects.get_or_create(
                        name=allergen_name
                    )

                    if not ingredient.allergens.filter(
                        pk=allergen.pk
                    ).exists():
                        ingredient.allergens.add(allergen)
                        added_relationships += 1

        self.stdout.write("")
        self.stdout.write(
            f"Ingredients matched: {mapped_ingredients}"
        )
        self.stdout.write(
            f"New relationships added: {added_relationships}"
        )
        self.stdout.write(
            f"Ingredients requiring review: {len(unmatched)}"
        )

        if unmatched:
            self.stdout.write("\nUnmatched ingredients:")
            for name in unmatched:
                self.stdout.write(f"  - {name}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nDRY RUN: No database changes made."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAllergen mapping completed."
                )
            )

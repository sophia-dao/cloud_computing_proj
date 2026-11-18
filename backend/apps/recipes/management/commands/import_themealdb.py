
import random
import re
import string
from decimal import Decimal, InvalidOperation
from fractions import Fraction

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.users.models import Allergen


API_URL = "https://www.themealdb.com/api/json/v1/1/search.php"
LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"
MEAL_ID_PATTERN = re.compile(r"Meal ID:\s*(\d+)")

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





def parse_measurement(raw):
    """Return (quantity, unit, notes) without guessing."""
    raw = (raw or "").strip()
    if not raw:
        return None, None, None

    normalized = raw.translate(str.maketrans({
        "½": "1/2",
        "¼": "1/4",
        "¾": "3/4",
    }))

    match = re.match(
        r"^(\d+(?:\.\d+)?|\d+/\d+)"
        r"(?:\s+(\d+/\d+))?\s*(.*)$",
        normalized,
    )

    if not match:
        return None, None, raw[:255]

    try:
        quantity = Decimal(str(Fraction(match.group(1))))
        if match.group(2):
            quantity += Decimal(str(Fraction(match.group(2))))
    except (ValueError, InvalidOperation, ZeroDivisionError):
        return None, None, raw[:255]

    remainder = match.group(3).strip()

    if quantity <= 0 or quantity > Decimal("99999.999"):
        return None, None, raw[:255]

    if not remainder:
        return quantity, None, None

    units = {
        "g", "kg", "mg", "ml", "l", "oz", "lb",
        "cup", "cups", "tsp", "tbsp", "teaspoon",
        "teaspoons", "tablespoon", "tablespoons",
        "pinch", "pinches", "clove", "cloves",
        "piece", "pieces", "can", "cans",
    }

    parts = remainder.split(maxsplit=1)

    if parts[0].lower() in units:
        unit = parts[0][:32]
        notes = parts[1][:255] if len(parts) > 1 else None
        return quantity, unit, notes

    return quantity, None, remainder[:255]


class Command(BaseCommand):
    help = "Import recipes from TheMealDB into Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Maximum number of new meals (0 = all).",
        )

        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Do not download recipe images.",
        )

        parser.add_argument(
            "--random",
            action="store_true",
            help="Import randomly selected meals instead of alphabetical order.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        if limit < 0:
            raise CommandError("--limit must be nonnegative.")

        created = 0
        skipped = 0
        seen = set()

        session = requests.Session()

        try:
            if options["random"]:
                # Random mode: collect all candidates before shuffling.
                all_meals = []

                for letter in string.ascii_lowercase:
                    meals = self.fetch_meals(session, letter)
                    all_meals.extend(meals)

                self.stdout.write(
                    f"Fetched {len(all_meals)} candidate recipes."
                )

                random.shuffle(all_meals)

                self.stdout.write(
                    "Randomized recipe import order."
                )

                meal_batches = [all_meals]

            else:
                # Default mode: fetch and import alphabetically.
                # This avoids fetching unnecessary letters when
                # --limit is small.
                meal_batches = (
                    self.fetch_meals(session, letter)
                    for letter in string.ascii_lowercase
                )

            for meals in meal_batches:
                for meal in meals:
                    meal_id = str(
                        meal.get("idMeal") or ""
                    ).strip()

                    name = (
                        meal.get("strMeal") or ""
                    ).strip()

                    if not meal_id or not name or meal_id in seen:
                        skipped += 1
                        continue

                    seen.add(meal_id)

                    # Avoid overwriting existing or user-owned recipes.
                    if Recipe.objects.filter(
                        name__iexact=name[:200]
                    ).exists():
                        skipped += 1
                        continue

                    instructions = (
                        meal.get("strInstructions") or ""
                    ).strip()

                    if not instructions:
                        skipped += 1
                        continue

                    # Ingredient-based recommendations require
                    # at least one valid ingredient.
                    ingredient_names = [
                        (
                            meal.get(f"strIngredient{i}") or ""
                        ).strip()
                        for i in range(1, 21)
                    ]

                    if not any(ingredient_names):
                        skipped += 1
                        continue

                    with transaction.atomic():
                        recipe = Recipe.objects.create(
                            owner=None,
                            name=name[:200],
                            instructions=instructions,
                            description=(
                                "Imported from TheMealDB "
                                f"(Meal ID: {meal_id})."
                            ),
                        )

                        # Import cuisine and category tags.
                        for field, tag_type in (
                            ("strArea", Tag.TagType.CUISINE),
                            ("strCategory", Tag.TagType.OTHER),
                        ):
                            value = (
                                meal.get(field) or ""
                            ).strip()

                            if value:
                                tag, _ = Tag.objects.get_or_create(
                                    name=value[:50],
                                    type=tag_type,
                                )

                                recipe.tags.add(tag)

                        # Import ingredients and measurements.
                        for i, ingredient_name in enumerate(
                            ingredient_names, start=1
                        ):
                            if not ingredient_name:
                                continue

                            normalized_name = ingredient_name[:255]

                            ingredient = Ingredient.objects.filter(
                                name__iexact=normalized_name
                            ).first()

                            if ingredient is None:
                                ingredient = Ingredient.objects.create(
                                    name=normalized_name
                                )

                            measure = meal.get(
                                f"strMeasure{i}"
                            )

                            quantity, unit, notes = parse_measurement(
                                measure
                            )

                            RecipeIngredient.objects.get_or_create(
                                recipe=recipe,
                                ingredient=ingredient,
                                defaults={
                                    "quantity": quantity,
                                    "unit": unit,
                                    "notes": notes,
                                },
                            )

                    # Images are optional and downloaded after
                    # the database transaction.
                    if not options["skip_images"]:
                        image_url = meal.get("strMealThumb")

                        if (
                            image_url
                            and image_url.startswith(
                                "https://www.themealdb.com/"
                            )
                        ):
                            try:
                                image_response = session.get(
                                    image_url,
                                    timeout=20,
                                )

                                image_response.raise_for_status()

                                if len(image_response.content) > 5_000_000:
                                    raise ValueError(
                                        "Image too large"
                                    )

                                recipe.image.save(
                                    f"themealdb_{meal_id}.jpg",
                                    ContentFile(
                                        image_response.content
                                    ),
                                    save=True,
                                )

                            except (
                                requests.RequestException,
                                ValueError,
                            ) as exc:
                                self.stderr.write(
                                    f"Image skipped for {name}: {exc}"
                                )

                    created += 1
                    self.stdout.write(
                        f"Imported: {name}"
                    )

                    if limit and created >= limit:
                        break

                if limit and created >= limit:
                    break

        finally:
            session.close()

        # Repair missing images from earlier imports, including reruns.
        if not options["skip_images"]:
            self.backfill_images()

        # Apply known allergen associations to imported ingredients.
        self.map_allergens()

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished: {created} imported, "
                f"{skipped} skipped."
            )
        )

    def fetch_meals(self, session, letter):
        """Fetch recipes beginning with a given letter."""
        try:
            response = session.get(
                API_URL,
                params={"f": letter},
                timeout=20,
            )

            response.raise_for_status()

            meals = response.json().get("meals") or []

            if not isinstance(meals, list):
                raise ValueError("Invalid meals response")

            return meals

        except (
            requests.RequestException,
            ValueError,
        ) as exc:
            raise CommandError(
                f"Failed fetching letter {letter}: {exc}"
            ) from exc

    def backfill_images(self):
        recipes = Recipe.objects.filter(
            Q(image__isnull=True) | Q(image=""),
            description__contains="Imported from TheMealDB",
        ).order_by("id")
        updated = 0
        skipped = 0
        with requests.Session() as session:
            for recipe in recipes.iterator():
                match = MEAL_ID_PATTERN.search(recipe.description or "")
                if not match:
                    skipped += 1
                    continue
                meal_id = match.group(1)
                try:
                    response = session.get(LOOKUP_URL, params={"i": meal_id}, timeout=20)
                    response.raise_for_status()
                    meals = response.json().get("meals") or []
                    if not meals:
                        skipped += 1
                        continue
                    image_url = meals[0].get("strMealThumb")
                    if not image_url or not image_url.startswith("https://www.themealdb.com/"):
                        skipped += 1
                        continue
                    image_response = session.get(image_url, timeout=20)
                    image_response.raise_for_status()
                    if len(image_response.content) > 5_000_000:
                        raise ValueError("Image exceeds 5 MB")
                    recipe.image.save(
                        f"themealdb_{meal_id}.jpg",
                        ContentFile(image_response.content),
                        save=True,
                    )
                    updated += 1
                except (requests.RequestException, ValueError) as exc:
                    skipped += 1
                    self.stderr.write(f"Image skipped for {recipe.name}: {exc}")
        self.stdout.write(f"Image backfill: {updated} updated, {skipped} skipped.")

    def map_allergens(self):
        matched = 0
        added = 0
        unmatched = 0
        with transaction.atomic():
            for ingredient in Ingredient.objects.all().iterator():
                detected = detect_allergens(ingredient.name)
                if not detected:
                    unmatched += 1
                    continue
                matched += 1
                for name in detected:
                    allergen, _ = Allergen.objects.get_or_create(name=name)
                    if not ingredient.allergens.filter(pk=allergen.pk).exists():
                        ingredient.allergens.add(allergen)
                        added += 1
        self.stdout.write(
            f"Allergen mapping: {matched} ingredients matched, "
            f"{added} relationships added, {unmatched} unmatched."
        )

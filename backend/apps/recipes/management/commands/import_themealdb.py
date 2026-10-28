
import re
import string
from decimal import Decimal, InvalidOperation
from fractions import Fraction

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, Tag


API_URL = "https://www.themealdb.com/api/json/v1/1/search.php"


def parse_measurement(raw):
    """Return (quantity, unit, notes) without guessing."""
    raw = (raw or "").strip()
    if not raw:
        return None, None, None

    normalized = raw.translate(str.maketrans({
        "½": "1/2", "¼": "1/4", "¾": "3/4"
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
            "--limit", type=int, default=0,
            help="Maximum number of meals (0 = all)."
        )
        parser.add_argument(
            "--skip-images", action="store_true",
            help="Do not download recipe images."
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 0:
            raise CommandError("--limit must be nonnegative.")

        created = 0
        skipped = 0
        seen = set()
        session = requests.Session()

        for letter in string.ascii_lowercase:
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
            except (requests.RequestException, ValueError) as exc:
                raise CommandError(
                    f"Failed fetching letter {letter}: {exc}"
                ) from exc

            for meal in meals:
                meal_id = str(meal.get("idMeal") or "").strip()
                name = (meal.get("strMeal") or "").strip()

                if not meal_id or not name or meal_id in seen:
                    skipped += 1
                    continue

                seen.add(meal_id)

                # Our schema has no external source ID.
                # Avoid overwriting existing or user-owned recipes.
                if Recipe.objects.filter(
                    name__iexact=name
                ).exists():
                    skipped += 1
                    continue

                instructions = (
                    meal.get("strInstructions") or ""
                ).strip()

                if not instructions:
                    skipped += 1
                    continue

                with transaction.atomic():
                    recipe = Recipe.objects.create(
                        owner=None,
                        name=name[:200],
                        instructions=instructions,
                        description=(
                            f"Imported from TheMealDB "
                            f"(Meal ID: {meal_id})."
                        ),
                    )

                    for field, tag_type in (
                        ("strArea", Tag.TagType.CUISINE),
                        ("strCategory", Tag.TagType.OTHER),
                    ):
                        value = (meal.get(field) or "").strip()
                        if value:
                            tag, _ = Tag.objects.get_or_create(
                                name=value[:50],
                                type=tag_type,
                            )
                            recipe.tags.add(tag)

                    for i in range(1, 21):
                        ingredient_name = (
                            meal.get(f"strIngredient{i}") or ""
                        ).strip()

                        if not ingredient_name:
                            continue

                        ingredient = Ingredient.objects.filter(
                            name__iexact=ingredient_name
                        ).first()

                        if ingredient is None:
                            ingredient = Ingredient.objects.create(
                                name=ingredient_name[:255]
                            )

                        measure = meal.get(f"strMeasure{i}")
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

                if not options["skip_images"]:
                    image_url = meal.get("strMealThumb")
                    if image_url and image_url.startswith(
                        "https://www.themealdb.com/"
                    ):
                        try:
                            image_response = session.get(
                                image_url, timeout=20
                            )
                            image_response.raise_for_status()
                            if len(image_response.content) > 5_000_000:
                                raise ValueError("Image too large")
                            recipe.image.save(
                                f"themealdb_{meal_id}.jpg",
                                ContentFile(image_response.content),
                                save=True,
                            )
                        except (requests.RequestException, ValueError) as exc:
                            self.stderr.write(
                                f"Image skipped for {name}: {exc}"
                            )

                created += 1
                self.stdout.write(f"Imported: {name}")

                if limit and created >= limit:
                    break

            if limit and created >= limit:
                break

        self.stdout.write(self.style.SUCCESS(
            f"Finished: {created} imported, {skipped} skipped."
        ))

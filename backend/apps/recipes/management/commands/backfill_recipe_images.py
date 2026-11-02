
import re

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.recipes.models import Recipe


MEAL_ID_PATTERN = re.compile(r"Meal ID:\s*(\d+)")
LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"


class Command(BaseCommand):
    help = "Backfill missing images for recipes imported from TheMealDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Maximum recipes to process (0 = all).",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview eligible recipes without downloading images.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        if limit < 0:
            self.stderr.write("--limit must be nonnegative.")
            return

        recipes = Recipe.objects.filter(
            Q(image__isnull=True) | Q(image="")
        ).filter(
            description__contains="Imported from TheMealDB"
        ).order_by("id")

        if limit:
            recipes = recipes[:limit]

        updated = 0
        skipped = 0

        with requests.Session() as session:
            for recipe in recipes:
                match = MEAL_ID_PATTERN.search(recipe.description or "")

                if not match:
                    skipped += 1
                    continue

                meal_id = match.group(1)

                if options["dry_run"]:
                    self.stdout.write(
                        f"Would update: {recipe.name} (Meal ID: {meal_id})"
                    )
                    continue

                try:
                    response = session.get(
                        LOOKUP_URL,
                        params={"i": meal_id},
                        timeout=20,
                    )
                    response.raise_for_status()

                    meals = response.json().get("meals") or []

                    if not meals:
                        skipped += 1
                        continue

                    image_url = meals[0].get("strMealThumb")

                    if not image_url or not image_url.startswith(
                        "https://www.themealdb.com/"
                    ):
                        skipped += 1
                        continue

                    image_response = session.get(
                        image_url,
                        timeout=20,
                    )
                    image_response.raise_for_status()

                    if len(image_response.content) > 5_000_000:
                        raise ValueError("Image exceeds 5 MB")

                    recipe.image.save(
                        f"themealdb_{meal_id}.jpg",
                        ContentFile(image_response.content),
                        save=True,
                    )

                    updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated: {recipe.name}"
                        )
                    )

                except (requests.RequestException, ValueError) as exc:
                    skipped += 1
                    self.stderr.write(
                        f"Skipped {recipe.name}: {exc}"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished: {updated} updated, {skipped} skipped."
            )
        )

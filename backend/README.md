# Backend

Django + Django REST Framework backend for the Recipe Suggestion App.

For complete system architecture and requirements, see the documentation under [`../docs/`](../docs/).

## Backend Structure

The backend follows a **modular, object-oriented architecture**.

Major application domains are separated into Django apps, while business logic is kept separate from API and database concerns.

```text
backend/
├── manage.py
├── config/                     # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                       # Application domain modules
│   ├── users/                  # Profiles, preferences, allergies
│   ├── ingredients/            # Canonical Ingredient data
│   ├── inventory/              # User Ingredient inventory
│   ├── recipes/                # Recipes and RecipeIngredients
│   ├── recommendations/        # Recipe matching/recommendation logic
│   ├── reviews/                # Recipe reviews and ratings
│   └── shopping/               # Shopping lists and list items
│
├── tests/                      # Cross-module/integration tests
│
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Backend container definition
└── .env.example                # Required environment variables
```

> Some directories/files may be added incrementally as their features are implemented.

---

## Django App Structure

Each domain should keep its responsibilities separated.

A typical app may look like:

```text
apps/recipes/
├── migrations/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── services.py
├── permissions.py
├── admin.py
├── apps.py
└── tests/
```

Not every app must contain every file.

Add files only when the module requires them.

### Responsibilities

```text
models.py
    Database entities and relationships

serializers.py
    API input/output serialization and validation

views.py
    HTTP/API request handling

urls.py
    API route definitions

services.py
    Business logic and reusable operations

permissions.py
    Application authorization rules

tests/
    Unit and API tests for the module
```

---

## Layering

Backend code should generally follow:

```text
HTTP Request
     │
     ▼
View / API Layer
     │
     ▼
Serializer / Validation
     │
     ▼
Service / Business Logic
     │
     ▼
Model / Data Layer
     │
     ▼
PostgreSQL
```

Views should remain relatively thin.

Complex business rules should not be implemented directly inside views.

For example:

```text
RecommendationView
        │
        ▼
RecommendationSerializer
        │
        ▼
RecommendationService
        │
        ├── Ingredient data
        ├── Recipe data
        ├── Tag preferences
        └── Allergen data
```

---

## Canonical Domain Data

Three standardized concepts are reused throughout the backend:

```text
Ingredient
    What food or ingredient is this?

Tag
    How is a Recipe or User preference classified?

Allergen
    What structured allergy relationship exists?
```

Examples:

```text
Ingredient
├── Chicken Breast
├── Egg
└── White Rice

Tag
├── Halal       [DIET]
├── Vietnamese  [CUISINE]
├── Cheap       [COST]
└── Quick       [OTHER]

Allergen
├── Peanut
├── Milk
├── Soy
└── Shellfish
```

These concepts should not be treated as interchangeable.

---

## Core Domain Modules

### `users`

Responsible for:

- Application User records.
- User profiles.
- Tag-based User preferences.
- User allergies.
- Optional onboarding information.
- Application roles and permissions.
- Mapping authenticated Cognito identities to application Users.

Conceptually:

```text
User
 │
 ├── UserProfile
 ├── UserPreference ──→ Tag
 └── UserAllergy ─────→ Allergen
```

Authentication itself is provided by **Amazon Cognito**.

Django remains responsible for application authorization.

---

### `ingredients`

Responsible for:

- Canonical Ingredients.
- Ingredient normalization/resolution.
- Ingredient categories.
- Ingredient lookup/search.
- Ingredient-to-Allergen relationships where implemented.

Example:

```text
"Tyson Frozen Chicken Breast"
            ↓
Ingredient Resolution
            ↓
"Chicken Breast"
```

Canonical Ingredient entities are shared by:

```text
Inventory
Recipes
Recommendations
Shopping Lists
Allergen relationships
```

Do not create separate Ingredient representations for individual features.

---

### `inventory`

Responsible for authenticated users' persistent Ingredient inventories.

```text
User
  │
  ▼
InventoryItem
  │
  ▼
Ingredient
```

Guest Ingredient selections are temporary and are not stored as User inventory.

The backend derives the InventoryItem owner from the authenticated User.

The frontend should not submit an authoritative `user_id`.

---

### `recipes`

Responsible for:

- Recipes.
- Recipe ownership.
- RecipeIngredients.
- Cooking instructions.
- Recipe metadata.
- Recipe Tags.
- Manual Recipe creation.
- Recipe modification and deletion where authorized.

```text
User
  │
  │ owns
  ▼
Recipe
  │
  ├── RecipeIngredient ──→ Ingredient
  │
  └── Tag
```

Normal users may modify or delete only Recipes they own.

Administrators may receive broader permissions.

The backend derives Recipe ownership from the authenticated User.

The frontend should not submit an authoritative `owner_id`.

---

### `recommendations`

Responsible for recipe matching and recommendation business logic.

Both Guests and Registered Users use the same recommendation service.

```text
Guest Ingredients ──────────┐
                            │
                            ▼
                   RecommendationService
                            ▲
                            │
Saved User Inventory ───────┘
```

Normalized recommendation input may include:

```text
RecommendationInput
│
├── ingredients
├── match_mode
│   ├── AVAILABLE_ONLY
│   └── PARTIAL_MATCH
├── allergen_ids
├── tag_ids
└── other supported filters
```

Initial matching modes:

```text
AVAILABLE_ONLY
    All required Recipe Ingredients
    must be available.

PARTIAL_MATCH
    At least one required Recipe Ingredient
    overlaps with the available Ingredients.
```

The recommendation module should return results such as:

```text
Recipe
Match Score
Available Ingredients
Missing Ingredients
Optional Missing Ingredients
```

The frontend should not recalculate authoritative recommendation business logic.

---

### `reviews`

Responsible for:

- Recipe ratings.
- Review comments.
- Review ownership.
- Review management/moderation.

Guests may read Reviews.

Creating or modifying Reviews requires authentication.

```text
User
 │
 ▼
Review
 │
 ▼
Recipe
```

The backend derives the Review author from authentication.

A User may have at most one active Review per Recipe in the initial design.

---

### `shopping`

Responsible for:

- ShoppingLists.
- ShoppingListItems.
- Generating lists from missing Recipe Ingredients.

Temporary shopping-list generation may be used by Guests.

Persistent ShoppingLists belong to authenticated Users.

```text
ShoppingList
     │
     ▼
ShoppingListItem
     │
     ▼
Ingredient
```

Shopping-list functionality should reuse canonical Ingredient entities.

---

## Tags and Preferences

Persistent User preferences use standardized Tags.

Initial Tag types include:

```text
DIET
CUISINE
COST
OTHER
```

Examples:

```text
Halal       → DIET
Vegan       → DIET
Vietnamese  → CUISINE
Korean      → CUISINE
Cheap       → COST
Quick       → OTHER
```

Tags are reused by Recipes and User preferences.

```text
User
 │
 ▼
UserPreference
 │
 ▼
Tag
 ▲
 │
Recipe
```

Do not create separate free-text preference systems for diet, cuisine, or cost when the corresponding Tag exists.

---

## Allergens

Allergens remain separate from Tags.

```text
User
 │
 ▼
UserAllergy
 │
 ▼
Allergen
 ▲
 │
Ingredient
```

Recipe allergen information can therefore be derived through:

```text
Recipe
   │
   ▼
RecipeIngredient
   │
   ▼
Ingredient
   │
   ▼
Allergen
```

Allergy-related business logic should not rely only on manually assigned Recipe Tags.

---

## Authentication and Authorization

Authentication:

```text
User
  ↓
Amazon Cognito
  ↓
Authenticated Identity
  ↓
Django API
  ↓
Application User
```

Amazon Cognito determines the authenticated identity.

Django determines what that identity is authorized to do.

```text
Guest
  ↓
Registered User
  ↓
Administrator
```

A Registered User has all Guest functionality.

An Administrator has all Registered User functionality plus administrative functionality.

---

## Resource Ownership

Ownership must be derived from the authenticated User whenever possible.

Examples:

```text
POST /api/inventory/
→ InventoryItem.user = authenticated User

POST /api/recipes/
→ Recipe.owner = authenticated User

POST /api/saved-recipes/
→ SavedRecipe.user = authenticated User

POST /api/recipes/{id}/reviews/
→ Review.user = authenticated User

POST /api/shopping-lists/
→ ShoppingList.user = authenticated User
```

Do not trust client-provided ownership fields such as:

```text
user_id
owner_id
review_author_id
```

for resources whose ownership can be determined from authentication.

Authorization must always be enforced in Django.

---

## API

All backend API routes should use the `/api/` prefix.

Examples:

```text
/api/users/me/
/api/users/me/preferences/
/api/users/me/allergies/

/api/ingredients/
/api/tags/
/api/allergens/

/api/inventory/
/api/recipes/
/api/recommendations/
/api/saved-recipes/
/api/shopping-lists/
```

The complete API contract is documented in:

```text
docs/api-design.md
```

When implementing an endpoint, follow the API contract rather than creating an alternative request or response format inside an individual feature.

---

## Development Rules

When contributing to the backend:

1. Keep application domains separated.
2. Keep views focused on HTTP/API responsibilities.
3. Put reusable business logic in service classes/functions.
4. Use Django models for persistent domain entities.
5. Use serializers for API validation and representation.
6. Do not duplicate recommendation logic for Guests and Registered Users.
7. Use canonical `Ingredient` entities for Ingredient-based business logic.
8. Use standardized `Tag` entities for Recipe classifications and persistent User preferences.
9. Keep `Allergen` separate from `Tag`.
10. Derive resource ownership from the authenticated User.
11. Never trust client-provided ownership identifiers when ownership can be derived from authentication.
12. Enforce permissions in the backend, not only in React.
13. Do not store secrets directly in source code.
14. Add tests for important business logic and API behavior.
15. Avoid unnecessary dependencies between Django apps.
16. Follow the documented database and API contracts when implementing features.
17. Do not create separate representations of shared domain entities without an architectural reason.

---

## Testing Expectations

Important backend functionality should include automated tests.

Tests should cover areas such as:

```text
Ingredient APIs
Tag APIs
Allergen APIs
Inventory ownership
Recipe ownership
RecipeIngredient behavior
Recommendation modes
Tag filtering
Allergen filtering
Saved Recipes
Review ownership and uniqueness
Shopping-list ownership
Authentication requirements
Authorization rules
```

Postman may be used for manual API testing.

Automated Django/DRF tests remain the authoritative regression tests for backend behavior.

---

## Local Development

Create and activate the Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py migrate
```

Run the backend:

```bash
python manage.py runserver
```

The local API will normally be available at:

```text
http://127.0.0.1:8000/
```

API requests can be tested using Postman.

---

## Docker

The Django backend is designed to run inside Docker.

Conceptually:

```text
Django Source
     │
     ▼
Docker Image
     │
     ▼
Backend Container
```

Persistent application data must remain outside the container.

```text
Backend Container
      │
      ├── PostgreSQL / Amazon RDS
      └── Media / Amazon S3
```

The production Docker image must not contain persistent database data, uploaded media, or hardcoded production secrets.

Deployment details are documented in:

```text
../docs/aws-architecture.md
```

---

## Documentation

Before implementing a major feature, check the relevant design documentation:

```text
../docs/
├── requirements.md        # What the application must support
├── system-design.md       # Architecture and design philosophy
├── database-design.md     # Models and relationships
├── api-design.md          # REST API contract
└── aws-architecture.md    # AWS deployment architecture
```

The documentation hierarchy is:

```text
requirements.md
      ↓
database-design.md
      ↓
api-design.md
      ↓
system-design.md
      ↓
aws-architecture.md
```

If implementation requires a significant change from the documented architecture, discuss and document the change before introducing conflicting designs.
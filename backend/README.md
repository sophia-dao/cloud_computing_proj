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
├── compose.yaml                # Local Django + PostgreSQL services
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

The backend uses **PostgreSQL** as the default database for local development. PostgreSQL runs in Docker, while Django can run either locally in a Python virtual environment or inside a Docker container.

### Prerequisites

- Python and pip
- Docker Desktop with Docker Compose

### Environment Configuration

From the `backend/` directory, create a local environment file:

```bash
cp .env.example .env
```

Configure the required variables:

```dotenv
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=postgresql
DB_NAME=recipe_app
DB_USER=recipe_user
DB_PASSWORD=your-local-database-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Generate a Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The `.env` file contains local credentials and must not be committed to Git. The `.env.example` file contains placeholders and can be committed.

### Option A: Django Locally + PostgreSQL in Docker

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL:

```bash
docker compose up -d db
```

Apply database migrations:

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

### Option B: Django + PostgreSQL in Docker

Build and start both services:

```bash
docker compose up -d --build
```

Apply migrations inside the backend container:

```bash
docker compose exec backend python manage.py migrate
```

Check running services:

```bash
docker compose ps
```

View backend logs:

```bash
docker compose logs -f backend
```

In this configuration, Docker Compose provides the hostname `db` for PostgreSQL. The backend container uses `DB_HOST=db`, while Django running directly on the host uses `DB_HOST=127.0.0.1`.

### Database Verification

Verify the database connection:

```bash
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"
```

Expected output:

```text
postgresql
```

For Dockerized Django:

```bash
docker compose exec backend python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"
```

### Testing

Run the Django test suite:

```bash
python manage.py test
```

Or run the tests inside the backend container:

```bash
docker compose exec backend python manage.py test
```

### Database Persistence

PostgreSQL uses the Docker named volume `postgres_data` to persist database files.

Stop the containers without deleting database data:

```bash
docker compose down
```

**Warning:** `docker compose down -v` removes the named volume and deletes its stored database data.

Existing SQLite data is not automatically transferred to PostgreSQL. The local PostgreSQL database is also separate from the planned production Amazon RDS PostgreSQL database.

---

## Docker

The Django backend is containerized using the existing `Dockerfile`.

The Docker image contains the Django application, its Python dependencies, and Gunicorn. Persistent application data must remain outside the container.

### Local Container Architecture

```text
Docker Compose
    │
    ├── backend
    │    ├── Django + DRF
    │    └── Gunicorn :8000
    │           │
    │           ▼
    └── db (PostgreSQL :5432)
             │
             ▼
       postgres_data volume
```

Docker Compose manages two services:

- `backend`: Builds and runs the Django application using the existing Dockerfile.
- `db`: Runs PostgreSQL 17 with a persistent volume and database health check.

The backend service waits for PostgreSQL to become healthy before starting.

### Production Deployment

The existing AWS deployment uses a separately built Docker image stored in Amazon ECR and deployed to Amazon EC2.

The local Docker Compose configuration is intended for development and integration testing. It does not automatically change the AWS deployment.

The production architecture is planned to use Amazon RDS PostgreSQL for managed database storage. RDS provisioning, security configuration, and database migration are handled in a separate infrastructure task.

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
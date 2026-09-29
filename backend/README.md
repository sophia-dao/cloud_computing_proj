# Backend

Django + Django REST Framework backend for the Recipe Suggestion App.

For complete system architecture and requirements, see the documentation under [`../docs/`](../docs/).

## Backend Structure

The backend follows a **modular, object-oriented architecture**. Major application domains are separated into Django apps, while business logic is kept separate from API and database concerns.

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
│   ├── ingredients/            # Canonical ingredient data
│   ├── inventory/              # User ingredient inventory
│   ├── recipes/                # Recipes and recipe ingredients
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

Not every app must contain every file. Add files only when the module requires them.

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
        └── User preferences
```

---

## Core Domain Modules

### `users`

Responsible for:

- Application user records.
- User profiles.
- Dietary preferences.
- Allergies.
- Onboarding information.
- Application roles and permissions.

Authentication itself is provided by **Amazon Cognito**.

---

### `ingredients`

Responsible for:

- Canonical ingredients.
- Ingredient normalization/resolution.
- Ingredient categories.
- Ingredient lookup/search.

Example:

```text
"Tyson Frozen Chicken Breast"
            ↓
Ingredient Resolution
            ↓
"Chicken Breast"
```

---

### `inventory`

Responsible for authenticated users' persistent ingredient inventories.

```text
User
  │
  ▼
InventoryItem
  │
  ▼
Ingredient
```

Guest ingredient selections are temporary and are not stored as user inventory.

---

### `recipes`

Responsible for:

- Recipes.
- Recipe ingredients.
- Cooking instructions.
- Recipe metadata.
- Manual recipe creation.

```text
Recipe
   │
   ▼
RecipeIngredient
   │
   ▼
Ingredient
```

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

Initial matching modes:

```text
AVAILABLE_ONLY
    All required recipe ingredients
    must be available.

PARTIAL_MATCH
    Recipe uses some available ingredients
    and may require additional ingredients.
```

The recommendation module should return results such as:

```text
Recipe
Match Score
Available Ingredients
Missing Ingredients
Optional Missing Ingredients
```

The frontend should not recalculate recommendation business logic.

---

### `reviews`

Responsible for:

- Recipe ratings.
- Review comments.
- Review ownership.
- Review management/moderation.

Guests may read reviews.

Creating or modifying reviews requires authentication.

---

### `shopping`

Responsible for:

- Shopping lists.
- Shopping-list items.
- Generating lists from missing recipe ingredients.

Temporary shopping-list generation may be used by Guests.

Persistent shopping lists belong to authenticated users.

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

## API

All backend API routes should use the `/api/` prefix.

Examples:

```text
/api/ingredients/
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

---

## Development Rules

When contributing to the backend:

1. Keep application domains separated.
2. Keep views focused on HTTP/API responsibilities.
3. Put reusable business logic in service classes/functions.
4. Use Django models for persistent domain entities.
5. Use serializers for API validation and representation.
6. Do not duplicate recommendation logic for Guests and Registered Users.
7. Use canonical `Ingredient` entities for ingredient-based business logic.
8. Enforce permissions in the backend, not only in React.
9. Do not store secrets directly in source code.
10. Add tests for important business logic and API behavior.
11. Avoid unnecessary dependencies between Django apps.
12. Follow the documented database and API contracts when implementing features.

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

If implementation requires a significant change from the documented architecture, discuss and document the change before introducing conflicting designs.
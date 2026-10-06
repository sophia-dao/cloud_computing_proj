# API Design

## 1. Purpose

This document defines the REST API design for communication between the React frontend and Django REST Framework backend of the Recipe Suggestion App.

The API provides a consistent interface for:

- Authentication-aware application functionality.
- User profiles and onboarding.
- User preferences and allergies.
- Canonical ingredients.
- Recipe tags and classifications.
- User inventory.
- Recipes.
- Recipe recommendations.
- Saved recipes.
- Reviews and ratings.
- Shopping lists.
- Administrative functionality.

The API should remain independent of frontend presentation details.

---

# 2. API Architecture

The application follows a client-server architecture.

```text
React Frontend
      │
      │ HTTPS / JSON
      ▼
Django REST API
      │
      ▼
Application / Service Layer
      │
      ▼
Models / PostgreSQL
```

React shall not access the application database directly.

All persistent application data shall be accessed through defined backend APIs.

Amazon Cognito provides authentication identity, while Django remains responsible for application-specific authorization and resource ownership.

---

# 3. Base API Path

All application endpoints should use a common API prefix.

```text
/api/
```

Examples:

```text
/api/recipes/
/api/ingredients/
/api/tags/
/api/allergens/
/api/inventory/
/api/recommendations/
/api/shopping-lists/
```

During local development:

```text
http://localhost:8000/api/
```

The production or development AWS API URL will be determined by the deployment architecture.

---

# 4. Data Format

The API shall primarily use JSON for requests and responses.

Example:

```json
{
  "name": "Kimchi Fried Rice",
  "preparation_time": 10,
  "cooking_time": 15
}
```

Media uploads may use an appropriate file-upload mechanism rather than JSON-only requests.

Where domain entities such as Ingredients, Tags, or Allergens already exist, API requests should reference their canonical IDs rather than submit duplicate unrestricted text whenever practical.

For example:

```json
{
  "ingredient_id": 17
}
```

is preferred over:

```json
{
  "ingredient": "Chicken Breast"
}
```

when the canonical Ingredient already exists.

---

# 5. Authentication

Amazon Cognito is responsible for authenticating registered users.

The frontend shall obtain authentication credentials or tokens through Cognito and include the required authentication information when calling protected Django endpoints.

Conceptually:

```text
User
 │
 ▼
Amazon Cognito
 │
 ▼
Authentication Token
 │
 ▼
React
 │
 │ Authenticated API Request
 ▼
Django REST API
 │
 ▼
Validate Identity
 │
 ▼
Application User
```

After validating the authentication identity, Django associates the request with the corresponding application `User`.

Django remains responsible for:

- Application authorization.
- Resource ownership.
- Administrative permissions.
- Access to private application data.

Authentication credentials such as passwords shall not be managed through application-specific Django API endpoints.

---

# 6. Access Levels

API endpoints use three conceptual access levels.

| Access | Description |
| --- | --- |
| Public | Available to Guests, Registered Users, and Administrators |
| User | Requires an authenticated Registered User or Administrator |
| Admin | Requires administrative permission |

The access hierarchy is:

```text
Guest
  │
  ▼
Registered User
  │
  ▼
Administrator
```

An Administrator retains access to normal Registered User functionality.

Some User endpoints additionally enforce resource ownership.

For example, an authenticated user may modify their own recipe but not another user's recipe unless administrative permission allows it.

---

# 7. Resource Ownership and Authorization

Authentication establishes the current application user.

The backend shall derive resource ownership from the authenticated user rather than trusting ownership identifiers submitted by the client.

Examples:

```text
POST /api/inventory/
→ InventoryItem.user = authenticated user

POST /api/recipes/
→ Recipe.owner = authenticated user

POST /api/saved-recipes/
→ SavedRecipe.user = authenticated user

POST /api/recipes/{id}/reviews/
→ Review.user = authenticated user

POST /api/shopping-lists/
→ ShoppingList.user = authenticated user
```

Clients shall not control fields such as:

```text
user_id
owner_id
review_author_id
```

when those fields can be determined from authentication.

Conceptually:

```text
User A → User A private resource
✓ Allowed where applicable

User A → User B private resource
✗ Forbidden

Admin → Administrative operation
✓ Allowed with required permission
```

Authorization shall always be enforced by Django.

Hiding functionality in React is not sufficient security.

---

# 8. HTTP Methods

The API should follow standard REST conventions where practical.

| Method | Purpose |
| --- | --- |
| GET | Retrieve resources |
| POST | Create a resource or execute an operation |
| PATCH | Partially update a resource |
| PUT | Replace a resource where appropriate |
| DELETE | Delete a resource |

---

# 9. HTTP Status Codes

Common response status codes should include:

| Status | Meaning |
| --- | --- |
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `204 No Content` | Request succeeded without response body |
| `400 Bad Request` | Invalid request |
| `401 Unauthorized` | Authentication required or invalid |
| `403 Forbidden` | Authenticated but insufficient permission |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Request conflicts with existing state |
| `500 Internal Server Error` | Unexpected server error |

---

# 10. Error Responses

Errors should use a consistent JSON structure.

Example:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request could not be processed.",
    "details": {}
  }
}
```

Validation errors may provide field-specific information.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Some fields are invalid.",
    "details": {
      "rating": [
        "Rating must be between 1 and 5."
      ]
    }
  }
}
```

The exact implementation may use Django REST Framework conventions where appropriate.

---

# 11. Pagination

Endpoints returning potentially large collections should support pagination.

Examples include:

```text
GET /api/recipes/
GET /api/ingredients/
GET /api/tags/
GET /api/reviews/
```

Conceptually:

```json
{
  "count": 125,
  "next": "...",
  "previous": null,
  "results": []
}
```

The exact pagination size will be determined during implementation.

---

# 12. User and Profile API

## GET `/api/users/me/`

**Access:** User

Returns information about the currently authenticated application user.

Example:

```json
{
  "id": 15,
  "email": "user@example.com",
  "display_name": "Alex",
  "profile_image": null,
  "is_admin": false
}
```

Authentication-related identity information such as email may be obtained from the validated Cognito identity where appropriate.

Internal identifiers such as `cognito_subject` do not need to be exposed to the frontend unless required by a specific application feature.

---

## PATCH `/api/users/me/`

**Access:** User

Updates supported profile information for the current user.

Example:

```json
{
  "display_name": "Alex"
}
```

Users shall only be able to modify their own profile through this endpoint.

Authentication credentials are not modified through this endpoint.

---

# 13. Preferences API

Onboarding is optional.

Users who skip onboarding may configure the same information later through profile or settings functionality.

Persistent user preferences use canonical `Tag` entities.

## GET `/api/users/me/preferences/`

**Access:** User

Returns the authenticated user's saved preferences.

Example:

```json
{
  "preferences": [
    {
      "id": 4,
      "name": "Halal",
      "type": "DIET"
    },
    {
      "id": 8,
      "name": "Vietnamese",
      "type": "CUISINE"
    },
    {
      "id": 12,
      "name": "Cheap",
      "type": "COST"
    }
  ]
}
```

---

## PUT `/api/users/me/preferences/`

**Access:** User

Replaces the authenticated user's saved Tag preferences.

Example:

```json
{
  "tag_ids": [4, 8, 12]
}
```

The backend shall validate that each submitted ID references a valid supported Tag.

Using Tag IDs ensures that user preferences and recipe classifications share the same standardized vocabulary.

Guest users may use temporary Tag filters without creating persistent UserPreference records.

---

# 14. Allergy API

## GET `/api/users/me/allergies/`

**Access:** User

Returns the authenticated user's saved allergies.

Example:

```json
{
  "allergies": [
    {
      "id": 1,
      "name": "Peanut"
    },
    {
      "id": 4,
      "name": "Shellfish"
    }
  ]
}
```

---

## PUT `/api/users/me/allergies/`

**Access:** User

Replaces the authenticated user's saved allergy selections.

Example:

```json
{
  "allergen_ids": [1, 4]
}
```

The backend shall validate that submitted IDs reference valid Allergens.

Guest allergy selections may remain temporary.

---

# 15. Tag API

Tags provide standardized recipe classifications and user preferences.

Initial Tag types include:

```text
DIET
CUISINE
COST
OTHER
```

## GET `/api/tags/`

**Access:** Public

Returns supported Tags.

The endpoint may support filtering by Tag type.

Examples:

```text
GET /api/tags/
GET /api/tags/?type=DIET
GET /api/tags/?type=CUISINE
GET /api/tags/?type=COST
```

Example response:

```json
{
  "results": [
    {
      "id": 4,
      "name": "Halal",
      "type": "DIET"
    },
    {
      "id": 8,
      "name": "Vietnamese",
      "type": "CUISINE"
    }
  ]
}
```

---

## GET `/api/tags/{id}/`

**Access:** Public

Returns information about a specific Tag.

---

# 16. Allergen Reference API

Allergens are structured separately from Tags.

## GET `/api/allergens/`

**Access:** Public

Returns supported Allergens.

Example:

```json
{
  "results": [
    {
      "id": 1,
      "name": "Peanut"
    },
    {
      "id": 4,
      "name": "Shellfish"
    }
  ]
}
```

This endpoint allows Guests and authenticated users to select standardized allergen filters.

---

## GET `/api/allergens/{id}/`

**Access:** Public

Returns information about a specific Allergen.

---

# 17. Ingredient API

Ingredients are canonical application ingredients.

## GET `/api/ingredients/`

**Access:** Public

Returns or searches canonical ingredients.

Example:

```text
GET /api/ingredients/?search=chicken
```

Example response:

```json
{
  "results": [
    {
      "id": 17,
      "name": "Chicken Breast",
      "category": "Poultry"
    }
  ]
}
```

This endpoint may be used to implement ingredient search and autocomplete in the frontend.

Ingredient descriptions should resolve to canonical Ingredient entities before being used by persistent application functionality whenever possible.

---

## GET `/api/ingredients/{id}/`

**Access:** Public

Returns information about a specific canonical Ingredient.

Example:

```json
{
  "id": 17,
  "name": "Chicken Breast",
  "category": "Poultry"
}
```

---

# 18. Inventory API

Persistent inventory functionality requires authentication.

Guest ingredient selections remain temporary and do not require InventoryItem records.

## GET `/api/inventory/`

**Access:** User

Returns the authenticated user's saved inventory.

Example:

```json
{
  "results": [
    {
      "id": 101,
      "ingredient": {
        "id": 3,
        "name": "Egg"
      }
    },
    {
      "id": 102,
      "ingredient": {
        "id": 5,
        "name": "Kimchi"
      }
    }
  ]
}
```

---

## POST `/api/inventory/`

**Access:** User

Adds a canonical Ingredient to the authenticated user's inventory.

Example:

```json
{
  "ingredient_id": 3
}
```

The backend derives the inventory owner from the authenticated user.

Submitting an Ingredient already contained in the user's inventory may return an existing resource or `409 Conflict`, depending on implementation.

---

## DELETE `/api/inventory/{id}/`

**Access:** User

Removes an InventoryItem belonging to the authenticated user.

Users shall not be able to delete inventory items belonging to another user.

---

# 19. Recipe API

## GET `/api/recipes/`

**Access:** Public

Returns recipes.

The endpoint may support query parameters such as:

```text
?search=rice
?tag=8
?tag_type=CUISINE
```

Additional filtering capabilities may be introduced as implementation progresses.

User-facing convenience filters such as cuisine or dietary filters should internally resolve to the corresponding standardized Tags.

---

## GET `/api/recipes/{id}/`

**Access:** Public

Returns complete information for a recipe.

Example:

```json
{
  "id": 42,
  "owner": {
    "id": 15,
    "display_name": "Alex"
  },
  "name": "Kimchi Fried Rice",
  "description": "Quick fried rice with kimchi.",
  "preparation_time": 10,
  "cooking_time": 15,
  "ingredients": [
    {
      "ingredient": {
        "id": 3,
        "name": "Egg"
      },
      "quantity": 2,
      "unit": null,
      "is_optional": false,
      "notes": null
    },
    {
      "ingredient": {
        "id": 4,
        "name": "White Rice"
      },
      "quantity": 2,
      "unit": "cups",
      "is_optional": false,
      "notes": null
    }
  ],
  "tags": [
    {
      "id": 8,
      "name": "Korean",
      "type": "CUISINE"
    },
    {
      "id": 12,
      "name": "Cheap",
      "type": "COST"
    }
  ],
  "instructions": "...",
  "image": "...",
  "average_rating": 4.5
}
```

Allergen information may be included where useful and should be derived from structured Ingredient → Allergen relationships.

---

## POST `/api/recipes/`

**Access:** User

Creates a manually submitted recipe owned by the authenticated user.

Example:

```json
{
  "name": "Simple Egg Fried Rice",
  "description": "Quick fried rice.",
  "preparation_time": 10,
  "cooking_time": 15,
  "ingredients": [
    {
      "ingredient_id": 3,
      "quantity": 2,
      "unit": null,
      "is_optional": false,
      "notes": null
    },
    {
      "ingredient_id": 4,
      "quantity": 2,
      "unit": "cups",
      "is_optional": false,
      "notes": null
    }
  ],
  "tag_ids": [8, 12],
  "instructions": "..."
}
```

The client shall not submit `owner_id`.

The backend assigns:

```text
Recipe.owner = authenticated user
```

The backend shall validate:

- Required recipe fields.
- Canonical Ingredient IDs.
- Tag IDs.
- Ingredient relationship data.
- Other supported recipe constraints.

---

## PATCH `/api/recipes/{id}/`

**Access:** Owner/Admin

Updates a recipe.

Normal users may only modify recipes they own.

Administrators may receive broader recipe-management permissions.

The backend shall not allow a normal user to change recipe ownership through this endpoint.

---

## DELETE `/api/recipes/{id}/`

**Access:** Owner/Admin

Deletes a recipe where authorized.

Normal users may only delete recipes they own.

Administrators may receive broader recipe-management permissions.

---

# 20. Recommendation API

Recipe recommendation is available to both Guests and authenticated users.

Both use the same backend `RecommendationService`.

```text
Guest Ingredients ───────────┐
                             │
                             ▼
                    Recommendation API
                             │
                             ▼
                    RecommendationService
                             ▲
                             │
Saved User Inventory ────────┘
```

## POST `/api/recommendations/`

**Access:** Public

Generates recipe recommendations.

The endpoint supports two matching modes:

```text
AVAILABLE_ONLY
PARTIAL_MATCH
```

---

## 20.1 Guest Request

A Guest provides canonical Ingredient IDs directly.

Example:

```json
{
  "ingredients": [3, 4, 5, 6],
  "match_mode": "AVAILABLE_ONLY",
  "filters": {
    "allergen_ids": [],
    "tag_ids": []
  }
}
```

Guest filters remain temporary.

---

## 20.2 Guest Request with Filters

Example:

```json
{
  "ingredients": [3, 4, 5, 6],
  "match_mode": "PARTIAL_MATCH",
  "filters": {
    "allergen_ids": [1],
    "tag_ids": [4, 8]
  }
}
```

For example, the Tags may represent:

```text
4 → Halal [DIET]
8 → Korean [CUISINE]
```

---

## 20.3 Authenticated User Request

An authenticated user may request that the recommendation service use their saved inventory.

Example:

```json
{
  "use_saved_inventory": true,
  "match_mode": "PARTIAL_MATCH"
}
```

The backend may apply the user's saved:

```text
Inventory
Preferences → Tags
Allergies → Allergens
```

where appropriate.

The user may provide temporary filters that modify or override supported defaults for the current recommendation request.

---

## 20.4 Direct Ingredients for Authenticated Users

Authenticated users may still provide ingredients directly.

This allows a Registered User to perform a temporary search without modifying persistent inventory.

Example:

```json
{
  "ingredients": [3, 5, 6],
  "use_saved_inventory": false,
  "match_mode": "PARTIAL_MATCH"
}
```

---

## 20.5 AVAILABLE_ONLY

In `AVAILABLE_ONLY` mode, a recipe is eligible when every required recipe Ingredient is available to the user.

Conceptually:

```text
Required Recipe Ingredients ⊆ User Ingredients
```

Optional RecipeIngredients do not prevent eligibility.

---

## 20.6 PARTIAL_MATCH

In `PARTIAL_MATCH` mode, a recipe may be returned when at least one required Ingredient overlaps with the user's available Ingredients.

Conceptually:

```text
Required Recipe Ingredients ∩ User Ingredients ≠ ∅
```

Eligible recipes should be ranked according to their match quality.

---

## 20.7 Recommendation Response

Example:

```json
{
  "match_mode": "PARTIAL_MATCH",
  "results": [
    {
      "recipe": {
        "id": 42,
        "name": "Kimchi Fried Rice",
        "image": "..."
      },
      "match_score": 0.75,
      "available_ingredients": [
        {
          "id": 3,
          "name": "Egg"
        },
        {
          "id": 5,
          "name": "Kimchi"
        },
        {
          "id": 6,
          "name": "Soy Sauce"
        }
      ],
      "missing_ingredients": [
        {
          "id": 4,
          "name": "White Rice"
        }
      ],
      "optional_missing_ingredients": []
    }
  ]
}
```

The frontend should not need to recalculate ingredient matching.

The backend owns recommendation business logic.

Recommendation results do not need to be stored persistently for the initial implementation.

---

# 21. Saved Recipe API

## GET `/api/saved-recipes/`

**Access:** User

Returns recipes saved by the authenticated user.

---

## POST `/api/saved-recipes/`

**Access:** User

Saves a Recipe for the authenticated user.

Example:

```json
{
  "recipe_id": 42
}
```

The backend derives the User from authentication.

The same recipe cannot be saved multiple times by the same user.

---

## DELETE `/api/saved-recipes/{id}/`

**Access:** User

Removes a SavedRecipe belonging to the authenticated user.

A user shall not be able to remove another user's SavedRecipe relationship.

---

# 22. Review API

## GET `/api/recipes/{recipe_id}/reviews/`

**Access:** Public

Returns reviews for a Recipe.

The endpoint may support pagination.

---

## POST `/api/recipes/{recipe_id}/reviews/`

**Access:** User

Creates a Review for the authenticated user.

Example:

```json
{
  "rating": 5,
  "comment": "Easy and inexpensive."
}
```

The backend determines the Review author from the authenticated identity.

The frontend shall not submit another user's ID as the Review author.

A user may have at most one active Review per Recipe.

Attempting to create another Review for the same User and Recipe may return:

```text
409 Conflict
```

The existing Review may instead be updated.

---

## PATCH `/api/reviews/{id}/`

**Access:** Owner/Admin

Updates an authorized Review.

Normal users may only modify their own Reviews.

---

## DELETE `/api/reviews/{id}/`

**Access:** Owner/Admin

Deletes an authorized Review.

Administrators may have moderation permission for Reviews belonging to other users.

---

# 23. Shopping List API

Shopping-list generation is available to both Guests and authenticated users.

Persistent shopping-list management requires authentication.

---

## POST `/api/shopping-list/generate/`

**Access:** Public

Generates a temporary shopping list from missing Recipe Ingredients.

Example:

```json
{
  "recipe_id": 42,
  "available_ingredients": [3, 5, 6]
}
```

Example response:

```json
{
  "items": [
    {
      "ingredient": {
        "id": 4,
        "name": "White Rice"
      },
      "quantity": 2,
      "unit": "cups"
    }
  ]
}
```

This operation does not necessarily persist the generated list.

---

## GET `/api/shopping-lists/`

**Access:** User

Returns the authenticated user's saved ShoppingLists.

---

## POST `/api/shopping-lists/`

**Access:** User

Creates a persistent ShoppingList belonging to the authenticated user.

Example:

```json
{
  "name": "Weekend Groceries"
}
```

A generated temporary shopping list may later be persisted through authenticated shopping-list functionality.

---

## GET `/api/shopping-lists/{id}/`

**Access:** Owner

Returns a ShoppingList belonging to the authenticated user.

---

## PATCH `/api/shopping-lists/{id}/`

**Access:** Owner

Updates supported ShoppingList information.

Example:

```json
{
  "name": "Saturday Groceries"
}
```

---

## DELETE `/api/shopping-lists/{id}/`

**Access:** Owner

Deletes a ShoppingList belonging to the authenticated user.

---

## POST `/api/shopping-lists/{id}/items/`

**Access:** Owner

Adds a canonical Ingredient to a ShoppingList.

Example:

```json
{
  "ingredient_id": 4,
  "quantity": 2,
  "unit": "cups"
}
```

The submitted Ingredient ID shall reference an existing canonical Ingredient.

---

## PATCH `/api/shopping-lists/{id}/items/{item_id}/`

**Access:** Owner

Updates a ShoppingListItem.

Example:

```json
{
  "completed": true
}
```

Supported updates may also include quantity and unit.

---

## DELETE `/api/shopping-lists/{id}/items/{item_id}/`

**Access:** Owner

Removes an item from a ShoppingList.

The backend shall verify that both the ShoppingList and ShoppingListItem belong to resources accessible by the authenticated user.

---

# 24. Media Handling

Recipe images and profile images are stored outside PostgreSQL.

The API stores or returns references to externally stored media.

Conceptually:

```text
React
  │
  ▼
Django API
  │
  ├── PostgreSQL metadata
  │
  └── Media Storage
```

The exact upload mechanism may evolve with the AWS implementation.

The database shall not store large image binaries directly.

Detailed media-storage architecture is documented in `aws-architecture.md`.

---

# 25. Admin API

Administrative operations require administrative permission.

Possible endpoints include:

```text
/api/admin/users/
/api/admin/recipes/
/api/admin/reviews/
/api/admin/ingredients/
/api/admin/tags/
/api/admin/allergens/
```

Administrative functionality may support:

- Viewing and managing application users.
- Managing Recipes.
- Moderating Reviews.
- Managing canonical Ingredients.
- Managing supported Tags.
- Managing supported Allergens.
- Managing other supported application content.

Administrative authorization shall always be enforced by Django.

React UI visibility is not an authorization mechanism.

---

# 26. Endpoint Summary

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/api/users/me/` | User | Current application user |
| PATCH | `/api/users/me/` | User | Update own profile |
| GET/PUT | `/api/users/me/preferences/` | User | Manage Tag preferences |
| GET/PUT | `/api/users/me/allergies/` | User | Manage saved allergies |
| GET | `/api/tags/` | Public | List/filter Tags |
| GET | `/api/tags/{id}/` | Public | Tag details |
| GET | `/api/allergens/` | Public | List Allergens |
| GET | `/api/allergens/{id}/` | Public | Allergen details |
| GET | `/api/ingredients/` | Public | Search/list canonical Ingredients |
| GET | `/api/ingredients/{id}/` | Public | Ingredient details |
| GET | `/api/inventory/` | User | Get saved inventory |
| POST | `/api/inventory/` | User | Add InventoryItem |
| DELETE | `/api/inventory/{id}/` | Owner | Remove InventoryItem |
| GET | `/api/recipes/` | Public | Browse/search/filter Recipes |
| GET | `/api/recipes/{id}/` | Public | Recipe details |
| POST | `/api/recipes/` | User | Create Recipe |
| PATCH | `/api/recipes/{id}/` | Owner/Admin | Update Recipe |
| DELETE | `/api/recipes/{id}/` | Owner/Admin | Delete Recipe |
| POST | `/api/recommendations/` | Public | Generate recommendations |
| GET | `/api/saved-recipes/` | User | Get saved Recipes |
| POST | `/api/saved-recipes/` | User | Save Recipe |
| DELETE | `/api/saved-recipes/{id}/` | Owner | Unsave Recipe |
| GET | `/api/recipes/{id}/reviews/` | Public | Recipe Reviews |
| POST | `/api/recipes/{id}/reviews/` | User | Create Review |
| PATCH | `/api/reviews/{id}/` | Owner/Admin | Update Review |
| DELETE | `/api/reviews/{id}/` | Owner/Admin | Delete Review |
| POST | `/api/shopping-list/generate/` | Public | Generate temporary shopping list |
| GET | `/api/shopping-lists/` | User | Get saved ShoppingLists |
| POST | `/api/shopping-lists/` | User | Create ShoppingList |
| GET | `/api/shopping-lists/{id}/` | Owner | ShoppingList details |
| PATCH | `/api/shopping-lists/{id}/` | Owner | Update ShoppingList |
| DELETE | `/api/shopping-lists/{id}/` | Owner | Delete ShoppingList |
| POST | `/api/shopping-lists/{id}/items/` | Owner | Add ShoppingListItem |
| PATCH | `/api/shopping-lists/{id}/items/{item_id}/` | Owner | Update ShoppingListItem |
| DELETE | `/api/shopping-lists/{id}/items/{item_id}/` | Owner | Delete ShoppingListItem |
| Various | `/api/admin/...` | Admin | Administrative operations |

---

# 27. API Testing Strategy

## 27.1 Manual API Testing

Postman will be used as the primary manual API testing and collaboration tool.

The team should maintain a shared Postman collection organized by application domain.

```text
Recipe App API
│
├── Users / Profile
├── Preferences
├── Allergies
├── Tags
├── Ingredients
├── Inventory
├── Recipes
├── Recommendations
├── Saved Recipes
├── Reviews
├── Shopping Lists
└── Admin
```

Environment variables should be used rather than hardcoding API addresses.

Example local environment:

```text
base_url = http://localhost:8000
```

Requests can then use:

```text
{{base_url}}/api/recipes/
{{base_url}}/api/ingredients/
{{base_url}}/api/recommendations/
```

A separate AWS development environment can use the same collection with a different `base_url`.

Protected endpoint tests should include valid authentication information where required.

---

## 27.2 Automated Backend Tests

Django/DRF automated tests should verify:

- Endpoint behavior.
- Request validation.
- Authentication requirements.
- Authorization rules.
- Resource ownership.
- Canonical Ingredient usage.
- Tag and preference behavior.
- Allergy behavior.
- Recommendation logic.
- Inventory behavior.
- Recipe ownership.
- Review ownership and uniqueness.
- Shopping-list ownership and behavior.

Important business logic should not rely solely on manual Postman testing.

---

## 27.3 Authorization Tests

Authorization tests should explicitly verify that users cannot access or modify another user's private resources.

Examples:

```text
User A deletes User A InventoryItem
→ Allowed

User A deletes User B InventoryItem
→ Forbidden

User A edits User A Recipe
→ Allowed

User A edits User B Recipe
→ Forbidden

Admin edits Recipe where permitted
→ Allowed
```

These tests are particularly important because client-side UI restrictions are not security controls.

---

## 27.4 Recommendation Tests

Recommendation tests should verify both supported modes:

```text
AVAILABLE_ONLY
PARTIAL_MATCH
```

Tests should cover:

- Required Ingredient matching.
- Optional Ingredients.
- Missing Ingredients.
- Match scores.
- Guest Ingredient input.
- Saved User inventory.
- Tag filters.
- Allergen filters.
- Saved preferences where applicable.

---

## 27.5 Continuous Integration

GitHub Actions may be configured to automatically run tests when code is pushed or submitted through a pull request.

Conceptually:

```text
Developer
    │
    ▼
Git Push / Pull Request
    │
    ▼
GitHub Actions
    │
    ├── Backend Tests
    ├── API Tests
    └── Frontend Tests
```

This allows integration problems to be detected before changes are merged.

---

# 28. API Design Principles

The team should follow these rules when implementing API functionality.

## 28.1 Backend Owns Business Logic

React should not independently implement authoritative business rules.

For example:

```text
Ingredient matching
Recommendation scoring
Allergen filtering
Ownership validation
Authorization
```

belong in the backend.

---

## 28.2 Use Canonical IDs

Persistent relationships should reference canonical application entities.

For example:

```text
ingredient_id
tag_id
allergen_id
recipe_id
```

should be preferred over duplicated unrestricted names when the corresponding entity already exists.

---

## 28.3 Never Trust Client Ownership Fields

The client shall not decide who owns a resource.

Ownership shall be derived from authenticated identity.

```text
Authenticated User
       │
       ▼
Django Authorization
       │
       ▼
Resource Ownership
```

---

## 28.4 Guest and User Recommendation Logic Must Remain Shared

Guest and authenticated-user recommendations should use the same RecommendationService.

Only the source of the input differs:

```text
Guest
  │
  └── Temporary Ingredients
             │
             ▼
      RecommendationService
             ▲
             │
Registered User
  │
  └── Saved Inventory
```

---

## 28.5 Tags and Allergens Have Different Responsibilities

Tags represent standardized Recipe classifications and User preferences.

Examples:

```text
Vegan       → DIET
Korean      → CUISINE
Cheap       → COST
Quick       → OTHER
```

Allergens represent structured allergy information associated with Ingredients.

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

Allergy safety should not rely only on manually assigned Recipe Tags.

---

## 28.6 Keep API Contracts Stable

Frontend code should depend on documented API contracts rather than internal Django implementation details.

Changing a Django model should not automatically require changing the public API unless the application's contract has intentionally changed.

---

# 29. Core API Data Flow

The major application data flow can be summarized as:

```text
                     Amazon Cognito
                           │
                           ▼
React ──────────────→ Django REST API
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
     Application      Authorization    Service Layer
        User                                  │
          │                                   │
          │                         ┌─────────┴──────────┐
          │                         │                    │
          ▼                         ▼                    ▼
      PostgreSQL             Recommendation       Shopping List
                                  Service             Service
                                     │
                                     ▼
                              Canonical Data
                         Ingredient / Tag / Allergen
```

---

# 30. Related Documentation

```text
requirements.md
    ↓
What must the application do?

database-design.md
    ↓
How is persistent data represented?

api-design.md
    ↓
How does the frontend interact with backend functionality?

system-design.md
    ↓
How do application components and services work together?

aws-architecture.md
    ↓
How is the system deployed in AWS?
```
# API Design

## 1. Purpose

This document defines the REST API design for communication between the React frontend and Django REST Framework backend of the Recipe Suggestion App.

The API provides a consistent interface for:

- Authentication-aware application functionality.
- User profiles and onboarding.
- Ingredients.
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
/api/inventory/
/api/recommendations/
/api/shopping-lists/
```

During local development:

```text
http://localhost:8000/api/
```

The production/development AWS API URL will be determined by the deployment architecture.

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

---

# 5. Authentication

Amazon Cognito is responsible for authenticating registered users.

The frontend shall obtain authentication credentials/tokens through Cognito and include the required authentication information when calling protected Django endpoints.

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

Django remains responsible for application authorization.

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

---

# 7. HTTP Methods

The API should follow standard REST conventions where practical.

| Method | Purpose |
| --- | --- |
| GET | Retrieve resources |
| POST | Create a resource or execute an operation |
| PATCH | Partially update a resource |
| PUT | Replace a resource where appropriate |
| DELETE | Delete a resource |

---

# 8. HTTP Status Codes

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

# 9. Error Responses

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

# 10. Pagination

Endpoints returning potentially large collections should support pagination.

Examples include:

```text
GET /api/recipes/
GET /api/ingredients/
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

# 11. User and Profile API

## GET `/api/users/me/`

**Access:** User

Returns information about the currently authenticated application user.

Example response:

```json
{
  "id": 15,
  "email": "user@example.com",
  "display_name": "Alex",
  "avatar": null,
  "is_admin": false
}
```

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

---

# 12. Onboarding and Preferences API

Onboarding is optional.

Users who skip onboarding may configure the same information later through profile/settings functionality.

## GET `/api/users/me/preferences/`

**Access:** User

Returns saved application preferences.

---

## PATCH `/api/users/me/preferences/`

**Access:** User

Updates supported preferences.

Example:

```json
{
  "dietary_preferences": [
    "halal"
  ],
  "cuisine_preferences": [
    "vietnamese",
    "korean"
  ]
}
```

---

## GET `/api/users/me/allergies/`

**Access:** User

Returns the authenticated user's saved allergies.

---

## PUT `/api/users/me/allergies/`

**Access:** User

Updates the user's saved allergies.

Example:

```json
{
  "allergen_ids": [1, 4]
}
```

---

# 13. Ingredient API

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

This endpoint may be used to implement ingredient autocomplete in the frontend.

---

## GET `/api/ingredients/{id}/`

**Access:** Public

Returns information about a specific canonical ingredient.

---

# 14. Inventory API

Persistent inventory functionality requires authentication.

Guest ingredient selections remain temporary and do not require inventory API records.

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

Adds an ingredient to the authenticated user's inventory.

Example:

```json
{
  "ingredient_id": 3
}
```

---

## DELETE `/api/inventory/{id}/`

**Access:** User

Removes an inventory item belonging to the authenticated user.

Users shall not be able to delete inventory items belonging to another user.

---

# 15. Recipe API

## GET `/api/recipes/`

**Access:** Public

Returns recipes.

The endpoint may support query parameters such as:

```text
?search=rice
?cuisine=korean
?diet=vegan
```

Additional filters may be introduced as implementation progresses.

---

## GET `/api/recipes/{id}/`

**Access:** Public

Returns complete information for a recipe.

Example response:

```json
{
  "id": 42,
  "name": "Kimchi Fried Rice",
  "description": "...",
  "preparation_time": 10,
  "cooking_time": 15,
  "cuisine": "Korean",
  "ingredients": [
    {
      "ingredient": {
        "id": 3,
        "name": "Egg"
      },
      "quantity": 2,
      "unit": null,
      "optional": false
    }
  ],
  "instructions": "...",
  "image": "...",
  "average_rating": 4.5
}
```

---

## POST `/api/recipes/`

**Access:** User

Creates a manually submitted recipe.

Example:

```json
{
  "name": "Simple Egg Fried Rice",
  "description": "Quick fried rice.",
  "ingredients": [
    {
      "ingredient_id": 3,
      "quantity": 2,
      "unit": null,
      "optional": false
    },
    {
      "ingredient_id": 4,
      "quantity": 2,
      "unit": "cups",
      "optional": false
    }
  ],
  "instructions": "..."
}
```

The backend shall validate submitted recipe information.

---

## PATCH `/api/recipes/{id}/`

**Access:** User/Admin according to ownership and permissions

Updates a recipe.

Normal users should only be able to modify recipes they are authorized to modify.

Administrators may have broader recipe-management permissions.

---

## DELETE `/api/recipes/{id}/`

**Access:** User/Admin according to ownership and permissions

Deletes a recipe where authorized.

---

# 16. Recommendation API

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

## 16.1 Guest Request

A Guest provides ingredients directly.

Example:

```json
{
  "ingredients": [3, 4, 5, 6],
  "match_mode": "AVAILABLE_ONLY",
  "filters": {
    "allergens": [],
    "dietary_preferences": [],
    "cuisines": []
  }
}
```

---

## 16.2 Authenticated User Request

An authenticated user may request that the recommendation service use their saved inventory.

Example:

```json
{
  "use_saved_inventory": true,
  "match_mode": "PARTIAL_MATCH"
}
```

The backend may automatically apply saved allergies and dietary preferences where appropriate.

The user may also provide current filters that modify or override supported defaults for the current recommendation request.

---

## 16.3 Direct Ingredients for Authenticated Users

Authenticated users may still provide ingredients directly.

This allows a registered user to perform a temporary search without modifying their persistent inventory.

Example:

```json
{
  "ingredients": [3, 5, 6],
  "use_saved_inventory": false,
  "match_mode": "PARTIAL_MATCH"
}
```

---

## 16.4 Recommendation Response

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

The frontend should not need to recalculate the ingredient match.

The backend owns recommendation business logic.

---

# 17. Saved Recipe API

## GET `/api/saved-recipes/`

**Access:** User

Returns recipes saved by the authenticated user.

---

## POST `/api/saved-recipes/`

**Access:** User

Saves a recipe.

Example:

```json
{
  "recipe_id": 42
}
```

---

## DELETE `/api/saved-recipes/{id}/`

**Access:** User

Removes a recipe from the authenticated user's saved recipes.

---

# 18. Review API

## GET `/api/recipes/{recipe_id}/reviews/`

**Access:** Public

Returns reviews for a recipe.

---

## POST `/api/recipes/{recipe_id}/reviews/`

**Access:** User

Creates a review for the authenticated user.

Example:

```json
{
  "rating": 5,
  "comment": "Easy and inexpensive."
}
```

The backend determines the review author from the authenticated identity.

The frontend shall not submit another user's ID as the review author.

---

## PATCH `/api/reviews/{id}/`

**Access:** User/Admin according to permissions

Updates an authorized review.

---

## DELETE `/api/reviews/{id}/`

**Access:** User/Admin according to permissions

Deletes an authorized review.

Administrators may have moderation permissions for reviews belonging to other users.

---

# 19. Shopping List API

Shopping-list generation is available to both Guests and authenticated users.

Persistent shopping-list management requires authentication.

## POST `/api/shopping-list/generate/`

**Access:** Public

Generates a temporary shopping list from missing recipe ingredients.

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

Returns the authenticated user's saved shopping lists.

---

## POST `/api/shopping-lists/`

**Access:** User

Creates a persistent shopping list.

A generated temporary shopping list may be submitted to this endpoint for persistence.

---

## GET `/api/shopping-lists/{id}/`

**Access:** User

Returns a shopping list belonging to the authenticated user.

---

## PATCH `/api/shopping-lists/{id}/`

**Access:** User

Updates supported shopping-list information.

---

## DELETE `/api/shopping-lists/{id}/`

**Access:** User

Deletes a shopping list belonging to the authenticated user.

---

## POST `/api/shopping-lists/{id}/items/`

**Access:** User

Adds an item to a shopping list.

---

## PATCH `/api/shopping-lists/{id}/items/{item_id}/`

**Access:** User

Updates a shopping-list item.

This may include marking an item as completed.

---

## DELETE `/api/shopping-lists/{id}/items/{item_id}/`

**Access:** User

Removes an item from a shopping list.

---

# 20. Admin API

Administrative operations require administrative permission.

Possible endpoints include:

```text
/api/admin/users/
/api/admin/recipes/
/api/admin/reviews/
```

Administrative endpoints may support:

- Viewing and managing users.
- Managing recipes.
- Moderating reviews.
- Managing supported application content.

Administrative authorization shall always be enforced by Django.

Hiding administrative functionality in React is not sufficient security.

---

# 21. Endpoint Summary

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/api/users/me/` | User | Current user |
| PATCH | `/api/users/me/` | User | Update profile |
| GET/PATCH | `/api/users/me/preferences/` | User | Manage preferences |
| GET/PUT | `/api/users/me/allergies/` | User | Manage allergies |
| GET | `/api/ingredients/` | Public | Search/list ingredients |
| GET | `/api/ingredients/{id}/` | Public | Ingredient details |
| GET | `/api/inventory/` | User | Get saved inventory |
| POST | `/api/inventory/` | User | Add inventory item |
| DELETE | `/api/inventory/{id}/` | User | Remove inventory item |
| GET | `/api/recipes/` | Public | Browse/search recipes |
| GET | `/api/recipes/{id}/` | Public | Recipe details |
| POST | `/api/recipes/` | User | Create recipe |
| PATCH | `/api/recipes/{id}/` | Authorized | Update recipe |
| DELETE | `/api/recipes/{id}/` | Authorized | Delete recipe |
| POST | `/api/recommendations/` | Public | Generate recommendations |
| GET | `/api/saved-recipes/` | User | Saved recipes |
| POST | `/api/saved-recipes/` | User | Save recipe |
| DELETE | `/api/saved-recipes/{id}/` | User | Unsave recipe |
| GET | `/api/recipes/{id}/reviews/` | Public | Recipe reviews |
| POST | `/api/recipes/{id}/reviews/` | User | Create review |
| PATCH | `/api/reviews/{id}/` | Authorized | Update review |
| DELETE | `/api/reviews/{id}/` | Authorized | Delete review |
| POST | `/api/shopping-list/generate/` | Public | Generate temporary list |
| GET/POST | `/api/shopping-lists/` | User | Manage saved lists |
| GET/PATCH/DELETE | `/api/shopping-lists/{id}/` | User | Manage saved list |
| POST | `/api/shopping-lists/{id}/items/` | User | Add list item |
| PATCH/DELETE | `/api/shopping-lists/{id}/items/{item_id}/` | User | Manage list item |
| Various | `/api/admin/...` | Admin | Administrative operations |

---

# 22. API Testing Strategy

## Manual API Testing

Postman will be used as the primary manual API testing and collaboration tool.

The team should maintain a shared Postman collection organized by application domain.

```text
Recipe App API
│
├── Users / Profile
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

A separate AWS development environment can later use the same collection with a different `base_url`.

---

## Automated Backend Tests

Django/DRF automated tests should verify:

- Endpoint behavior.
- Request validation.
- Authentication requirements.
- Authorization rules.
- Resource ownership.
- Recommendation logic.
- Inventory behavior.
- Shopping-list behavior.

Important business logic should not rely solely on manual Postman testing.

---

## Continuous Integration

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

# 23. API Design Principles

The team should follow these rules when implementing API functionality:

1. Use consistent REST conventions.
2. Keep API endpoints independent of frontend presentation.
3. Enforce authentication and authorization on the backend.
4. Never trust a user ID supplied by the frontend when authenticated identity can determine ownership.
5. Validate all client-provided input.
6. Return consistent error responses.
7. Use canonical ingredient identifiers for application business logic where possible.
8. Avoid duplicating Guest and Registered User business logic.
9. Keep recommendation calculations in the backend.
10. Keep application business logic out of React components.
11. Avoid exposing unnecessary internal database implementation details.
12. Use pagination for potentially large collections.
13. Protect user-specific resources from access by other users.
14. Keep API contracts documented as endpoints evolve.
15. Add automated tests for important API behavior.

---

# 24. Related Documentation

```text
requirements.md
    ↓
Defines what the application must support

system-design.md
    ↓
Defines application architecture and responsibilities

database-design.md
    ↓
Defines entities used by API resources

api-design.md
    ↓
Defines frontend-backend communication

aws-architecture.md
    ↓
Defines where API components are deployed
```
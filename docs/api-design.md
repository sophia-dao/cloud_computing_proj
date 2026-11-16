# API Design — Recipe Suggestion App

## 1. Overview

The Recipe Suggestion App uses a REST API developed with Django REST Framework (DRF) to communicate between the React frontend and the Django backend.

The API handles recipe discovery, ingredient management, personal inventories, user preferences, allergies, saved recipes, recipe submissions, and recommendations.

The frontend communicates with the backend over HTTPS in production, with API requests routed through Amazon CloudFront to an internal Application Load Balancer.

### API Architecture

```text
React Frontend
      |
      | HTTPS / JSON
      v
Amazon CloudFront (/api/*)
      |
      v
Internal Application Load Balancer
      |
      v
Django REST Framework
      |
      +-- Application Logic
      +-- Authorization
      +-- PostgreSQL (Amazon RDS)
      +-- Recipe Images (Amazon S3)
```

The frontend does not communicate directly with the PostgreSQL database.

## 2. API Conventions

### Base URL

All application endpoints use the `/api/` prefix.

Local development:

```text
http://localhost:8000/api/
```

Production:

```text
https://d1q0iv2raorz8j.cloudfront.net/api/
```

### Data Format

Most API requests and responses use JSON.

Recipe image uploads may use `multipart/form-data`.

### HTTP Methods

| Method | Purpose |
|---|---|
| `GET` | Retrieve data |
| `POST` | Create data or perform an operation |
| `PATCH` | Update supported fields |
| `PUT` | Replace or update a resource where supported |
| `DELETE` | Remove a resource |

### Common Response Codes

| Code | Meaning |
|---|---|
| `200` | Request successful |
| `201` | Resource created |
| `204` | Resource deleted or request completed without a response body |
| `400` | Invalid request |
| `401` | Missing or invalid authentication |
| `403` | Insufficient permission |
| `404` | Resource not found |
| `500` | Unexpected server error |

Validation errors are returned using Django REST Framework response conventions.

## 3. Authentication and Authorization

Authentication is managed by Amazon Cognito User Pools, with Google Sign-In supported through Cognito federation.

The frontend uses the OAuth 2.0 Authorization Code flow with PKCE.

After successful authentication, the frontend sends the Cognito access token with protected API requests:

```http
Authorization: Bearer <access_token>
```

Django validates the Cognito JWT and maps the authenticated identity to a local application user using the token's issuer and subject.

### Access Levels

| Access | Description |
|---|---|
| Public | Available without authentication |
| Registered User | Requires a valid Cognito access token |
| Owner | Requires authentication and ownership of the resource |
| Admin | Requires application administrative permission |

Django enforces authentication, authorization, and resource ownership independently of frontend visibility restrictions.

### Current User

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/auth/me/` | Registered User | Returns information about the authenticated application user |

User passwords and Google authentication credentials are not managed through Django application endpoints.

## 4. Ingredients and Recipe Classifications

These endpoints provide reference data for ingredient selection, recipe filtering, and user preferences.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/ingredients/` | Public | List or search ingredients |
| `GET` | `/api/ingredients/{id}/` | Public | Retrieve ingredient details |
| `GET` | `/api/tags/` | Public | Retrieve recipe classifications |
| `GET` | `/api/users/allergens/` | Public | Retrieve supported allergens |

Tags provide classifications such as dietary categories, cuisine types, and cost levels.

Ingredients are represented using canonical records that can be reused across recipes, inventories, and recommendations.

## 5. Recipe API

The Recipe API provides recipe discovery, filtering, detailed information, and authenticated recipe submission.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/recipes/` | Public | Browse, search, and filter recipes |
| `GET` | `/api/recipes/{id}/` | Public | Retrieve recipe details |
| `POST` | `/api/recipes/` | Registered User | Submit a new recipe |

### Recipe Filtering

The recipe listing endpoint supports filtering based on supported recipe attributes, such as ingredients, classifications, and dietary restrictions.

Authenticated users' saved preferences and allergies are automatically applied to applicable recipe browsing requests.

Example:

```http
GET /api/recipes/?limit=12
```

### Recipe Submission

Registered users can submit recipes containing recipe details, ingredients, instructions, and an optional image where supported.

The backend validates required information and checks for duplicate recipe names.

Recipe ownership is determined from the authenticated user rather than from an arbitrary client-provided owner identifier.

Uploaded recipe images are stored using the application's Amazon S3 media storage integration.

## 6. Inventory API

The Inventory API allows registered users to manage their personal ingredients.

Supported operations include retrieving the saved inventory, adding ingredients, and removing existing inventory items.

Inventory data is associated with the authenticated user.

Guest ingredient selections do not require persistent inventory records.

## 7. Recommendations API

The recommendation system matches recipes against available ingredients.

It supports two matching modes:

| Mode | Behavior |
|---|---|
| `AVAILABLE_ONLY` | Returns recipes for which all required ingredients are available |
| `PARTIAL_MATCH` | Returns recipes with partially matching ingredients |

Recommendation processing is performed by the Django backend.

Depending on the request, ingredient data may come from temporary selections or a registered user's saved inventory.

Recommendation results can identify available and missing ingredients, allowing the frontend to display how well each recipe matches.

The results are generated dynamically rather than stored as persistent recommendation records.

## 8. User Preferences and Allergies

Registered users can manage their profile settings, dietary preferences, and allergies through authenticated APIs.

Saved preferences are associated with recipe classifications, while saved allergies are associated with recognized allergen records.

The backend uses this information to apply supported filtering rules to recipe browsing and recommendations.

User-specific settings are protected by authentication and ownership checks.

## 9. Saved Recipes API

The Saved Recipes feature allows authenticated users to maintain personal collections of recipes.

Supported operations include:

- Retrieving saved recipes.
- Saving an existing recipe.
- Removing a saved recipe.

Each saved-recipe relationship belongs to the authenticated user.

The backend prevents unauthorized access to another user's saved recipes and avoids duplicate saved relationships.

## 10. Testing and Validation

The backend was tested using Django's automated test framework and Django REST Framework testing utilities.

The final backend test run completed with **359 passing tests and one skipped test**.

Testing covered application functionality, including authentication, permissions, recipe management, ingredient handling, inventory, and recommendations.

API performance was also evaluated using ApacheBench with 1,000 requests at concurrency levels of 10, 50, and 100.

The load tests included recipe listing and recipe detail endpoints.

## 11. Future API Development

The following functionality remains outside the final implemented API scope:

- Recipe reviews and ratings.
- Shopping list management.
- Dedicated administrative management APIs and UI.
- Advanced recommendation and AI-assisted features.

These features may be added through future API extensions.

## 12. Related Documentation

- [Requirements](requirements.md) — Original functional requirements.
- [System Design](system-design.md) — Application components and architecture.
- [Database Design](database-design.md) — Database entities and relationships.
- [AWS Architecture](aws-architecture.md) — Production deployment and networking.
- [Main README](../README.md) — Project overview.
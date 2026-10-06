# System Design

## 1. Purpose

This document describes the high-level software architecture of the Recipe Suggestion App.

The system is designed as a cloud-hosted web application with:

- A React frontend.
- A Django REST Framework backend.
- PostgreSQL for persistent relational data.
- Amazon Cognito for authentication.
- External object storage for media.
- Dockerized backend deployment.
- AWS-based hosting and infrastructure.

The system is designed as a modular monolith for the initial implementation while preserving clear boundaries between major application domains.

This approach keeps the project manageable for the current team while allowing individual components to evolve or scale independently when necessary.

---

# 2. High-Level Architecture

The application follows a client-server architecture.

```text
                    User
                     │
                     ▼
               Web Browser
                     │
                     ▼
              React Frontend
                     │
                     │ HTTPS / REST / JSON
                     ▼
              Django REST API
                     │
          ┌──────────┼───────────┐
          │          │           │
          ▼          ▼           ▼
     PostgreSQL   Media      Amazon Cognito
                  Storage
```

The React frontend is responsible for user interaction and presentation.

The Django backend is responsible for:

- API behavior.
- Business logic.
- Authorization.
- Resource ownership.
- Data validation.
- Recommendation logic.
- Database interaction.
- Integration with supporting cloud services.

React shall not communicate directly with PostgreSQL.

Persistent application data shall be accessed through backend APIs.

---

# 3. Architectural Style

The backend uses a modular-monolith architecture.

```text
Django Backend
│
├── Users
├── Ingredients
├── Recipes
├── Inventory
├── Recommendations
├── Reviews
└── Shopping
```

These domains remain part of one Django application deployment but maintain clear responsibilities.

This approach was selected because:

- The project is being developed by a small team.
- The application does not initially require independent microservices.
- Django applications provide useful modular boundaries.
- Deployment remains simple.
- Business logic can be centralized where appropriate.
- Future architectural changes remain possible without introducing unnecessary complexity now.

The project should avoid premature conversion to microservices.

---

# 4. Major Application Domains

## 4.1 Users

The Users domain is responsible for application-specific user functionality.

Responsibilities include:

- Mapping authenticated Cognito identities to application Users.
- User profiles.
- User preferences.
- User allergies.
- Application permissions.
- Administrative status.
- User-specific authorization.

Amazon Cognito remains responsible for authentication identity.

Django remains responsible for application authorization.

---

## 4.2 Ingredients

The Ingredients domain manages canonical Ingredients used throughout the application.

Responsibilities include:

- Canonical Ingredient records.
- Ingredient search.
- Ingredient lookup.
- Ingredient categories.
- Ingredient normalization or resolution where supported.
- Ingredient-to-Allergen relationships.

Examples of canonical Ingredients include:

```text
Chicken Breast
White Rice
Egg
Kimchi
Soy Sauce
Garlic
Green Onion
```

The same Ingredient entities are reused by:

```text
Inventory
Recipes
Recommendations
Shopping Lists
Allergen relationships
```

The Ingredients domain therefore acts as a shared foundation rather than belonging only to Inventory.

---

## 4.3 Recipes

The Recipes domain manages recipe information.

Responsibilities include:

- Recipe creation.
- Recipe ownership.
- Recipe details.
- Recipe ingredients.
- Recipe classifications.
- Recipe search and filtering.
- Recipe modification.
- Recipe deletion.
- Saved-recipe relationships where appropriate.

Recipes reference canonical Ingredients through `RecipeIngredient`.

Recipes use standardized Tags for classifications such as:

```text
DIET
CUISINE
COST
OTHER
```

---

## 4.4 Inventory

The Inventory domain manages persistent Ingredient selections belonging to authenticated users.

Responsibilities include:

- Viewing saved inventory.
- Adding canonical Ingredients.
- Removing inventory items.
- Providing saved inventory to RecommendationService.

Guest Ingredient selections are temporary and do not create persistent Inventory records.

---

## 4.5 Recommendations

The Recommendations domain contains recipe-matching business logic.

Responsibilities include:

- `AVAILABLE_ONLY` matching.
- `PARTIAL_MATCH` matching.
- Match-score calculation.
- Missing-Ingredient calculation.
- Optional-Ingredient handling.
- Tag filtering.
- Allergen filtering.
- Reusing the same recommendation logic for Guests and authenticated users.

Recommendation results do not require persistent database storage for the initial implementation.

---

## 4.6 Reviews

The Reviews domain manages recipe ratings and comments.

Responsibilities include:

- Creating Reviews.
- Reading Reviews.
- Updating Reviews.
- Deleting Reviews.
- Review ownership.
- Rating validation.
- Administrative moderation.

The initial design allows one active Review per User per Recipe.

---

## 4.7 Shopping

The Shopping domain manages shopping-list functionality.

Responsibilities include:

- Generating missing-Ingredient lists.
- Temporary Guest shopping lists.
- Persistent authenticated-user ShoppingLists.
- ShoppingListItems.
- Completion state.
- Quantity and unit information where supported.

ShoppingListItems reference the same canonical Ingredient entities used elsewhere in the application.

---

# 5. Canonical Domain Data

Three standardized concepts are especially important across the system:

```text
                  Canonical Application Data


Ingredient                 Tag                 Allergen
    │                        │                     │
    ├── Inventory            ├── DIET              ├── Ingredient
    ├── Recipes              ├── CUISINE           │
    ├── Recommendations      ├── COST              └── UserAllergy
    └── Shopping Lists       └── OTHER
                             │
                             ├── Recipe
                             └── UserPreference
```

Their responsibilities are different.

## 5.1 Ingredient

Ingredient answers:

> What food or ingredient is this?

Examples:

```text
Chicken Breast
Egg
White Rice
Soy Sauce
```

Ingredients are canonical shared entities.

---

## 5.2 Tag

Tag answers:

> How is this Recipe or User preference classified?

Examples:

```text
Vegan        [DIET]
Halal        [DIET]
Korean       [CUISINE]
Vietnamese   [CUISINE]
Cheap        [COST]
Quick        [OTHER]
```

Tags are shared between Recipe classification and User preferences.

---

## 5.3 Allergen

Allergen answers:

> What structured allergy relationship exists for this Ingredient?

Examples:

```text
Peanut
Milk
Egg
Wheat
Soy
Shellfish
```

Allergens are associated with Ingredients.

Conceptually:

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

Allergy filtering should not depend only on manually assigned Recipe Tags.

---

# 6. Backend Structure

The Django backend should be organized around application domains.

Conceptually:

```text
backend/
│
├── config/
│
├── apps/
│   ├── users/
│   ├── ingredients/
│   ├── recipes/
│   ├── inventory/
│   ├── recommendations/
│   ├── reviews/
│   └── shopping/
│
├── manage.py
└── requirements/
```

Each Django application should contain the files appropriate to its responsibility.

For example:

```text
apps/ingredients/
│
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
└── tests/
```

Not every conceptual domain object requires a separate Django application.

For example, Tags and Allergens may initially live within the most appropriate existing application rather than introducing additional Django apps purely for structural symmetry.

Separate applications should be introduced only when their responsibilities justify the additional complexity.

---

# 7. Backend Layering

Backend request processing should follow a clear flow.

```text
HTTP Request
     │
     ▼
API / View Layer
     │
     ▼
Business / Service Layer
     │
     ▼
Domain / Models
     │
     ▼
Persistence
```

## 7.1 API / View Layer

Responsible for:

- Receiving requests.
- Authentication integration.
- Parsing input.
- Basic request validation.
- Calling appropriate business logic.
- Serializing responses.
- Returning HTTP status codes.

Views should avoid containing large amounts of business logic.

---

## 7.2 Business / Service Layer

The service layer contains application workflows and business rules that should not be duplicated across views.

Examples include:

```text
RecommendationService
ShoppingListService
IngredientResolutionService
```

Additional services may be introduced where application complexity justifies them.

---

## 7.3 Domain / Model Layer

The domain/model layer represents persistent application concepts and relationships.

Examples include:

```text
User
UserProfile
Ingredient
InventoryItem
Recipe
RecipeIngredient
SavedRecipe
Tag
UserPreference
Allergen
UserAllergy
Review
ShoppingList
ShoppingListItem
```

Detailed relationships are defined in `database-design.md`.

---

# 8. Frontend Architecture

The React frontend should use a feature-oriented organization.

Conceptually:

```text
frontend/src/
│
├── app/
│
├── components/
│   ├── common/
│   └── layout/
│
├── features/
│   ├── ingredients/
│   ├── recommendations/
│   ├── recipes/
│   ├── inventory/
│   ├── profile/
│   ├── reviews/
│   └── shopping/
│
├── pages/
│
├── services/
│
└── App.jsx
```

The exact structure may evolve as implementation progresses.

---

# 9. Frontend Responsibilities

React is responsible for:

- Rendering pages.
- Handling user interactions.
- Routing.
- Form state.
- Temporary Guest state.
- Calling backend APIs.
- Displaying validation errors.
- Displaying recommendation results.
- Presenting authenticated-user functionality.

React should not contain authoritative implementations of backend business rules.

For example, React should not independently determine:

- Whether a Recipe qualifies for `AVAILABLE_ONLY`.
- The authoritative recommendation match score.
- Whether a Recipe is safe for a saved allergy.
- Whether a User owns a Recipe.
- Whether a User has administrative permission.

Those decisions belong to Django.

---

# 10. API Service Layer in React

Frontend API calls should be centralized rather than scattered throughout components.

Conceptually:

```text
React Component
      │
      ▼
Feature Service
      │
      ▼
Shared API Client
      │
      ▼
Django REST API
```

Examples:

```text
ingredientService
recipeService
recommendationService
inventoryService
userService
shoppingListService
```

A shared API client may manage:

- Base API URL.
- JSON handling.
- Authentication headers.
- Common error handling.

Detailed endpoint contracts are documented in `api-design.md`.

---

# 11. Authentication Architecture

Amazon Cognito provides authentication identity.

Django maintains the application-specific User and authorization model.

Conceptually:

```text
User
 │
 ▼
React
 │
 ▼
Amazon Cognito
 │
 │ Authenticate
 ▼
Authentication Identity / Token
 │
 ▼
React
 │
 │ Authenticated API Request
 ▼
Django
 │
 │ Validate Identity
 ▼
Application User
```

The application User is associated with the corresponding Cognito identity using a stable external identifier.

Authentication credentials are not stored in application-specific PostgreSQL User records.

---

# 12. Authentication vs. Authorization

Authentication and authorization have separate responsibilities.

```text
Amazon Cognito
      │
      └── Who is this user?


Django
      │
      └── What may this user do?
```

Cognito handles authentication.

Django handles:

- Resource ownership.
- Application permissions.
- Administrative privileges.
- Private-data access.
- Protected API operations.

React may hide unavailable UI functionality, but React is not a security boundary.

---

# 13. Application User Mapping

After Django validates a Cognito-authenticated request, it maps the identity to an application User.

Conceptually:

```text
Validated Cognito Identity
           │
           │ stable external identifier
           ▼
     Application User
           │
           ├── Profile
           ├── Inventory
           ├── Preferences
           ├── Allergies
           ├── Saved Recipes
           ├── Reviews
           └── Shopping Lists
```

This separation prevents Cognito from becoming the storage system for application-specific domain data.

---

# 14. Authorization and Resource Ownership

The backend derives resource ownership from authenticated identity.

The frontend should not be trusted to submit ownership information for resources whose owner can be determined from authentication.

For example:

```text
POST Recipe
     │
     ▼
Authenticated User
     │
     ▼
Recipe.owner
```

The client does not determine `owner_id`.

Similarly:

```text
Authenticated User
       │
       ├── InventoryItem.user
       ├── SavedRecipe.user
       ├── Review.user
       └── ShoppingList.user
```

Typical authorization behavior:

```text
Recipe Read
    │
    └── Public

Recipe Create
    │
    └── Registered User

Recipe Update/Delete
    │
    ├── Owner
    └── Administrator
```

And:

```text
User A → User A private resource
✓ Allowed where applicable

User A → User B private resource
✗ Forbidden

Administrator → protected administrative operation
✓ Allowed with required permission
```

All authorization checks must be enforced by Django.

---

# 15. Guest Architecture

Guests can use the main recommendation workflow without creating an account.

Guest state remains temporary.

Conceptually:

```text
Guest
 │
 ▼
React Temporary State
 │
 ├── Ingredient IDs
 ├── Tag Filters
 ├── Allergen Filters
 └── Match Mode
 │
 ▼
Recommendation API
 │
 ▼
RecommendationService
```

Guest state may be stored temporarily in:

- React component state.
- React application state.
- Browser session storage.
- Another appropriate non-persistent client mechanism.

Guest data does not require persistent PostgreSQL User records.

---

# 16. Registered User Architecture

Registered Users use the same core services but may persist data.

```text
Authenticated User
      │
      ▼
Django Application User
      │
      ├── Profile
      ├── Inventory
      ├── UserPreferences
      ├── UserAllergies
      ├── SavedRecipes
      ├── Reviews
      └── ShoppingLists
```

The recommendation algorithm remains shared between Guests and Registered Users.

Only the source and persistence of input data differ.

---

# 17. Onboarding Architecture

Onboarding is optional.

After account creation, the application may ask for:

```text
Optional Onboarding
      │
      ├── Allergies
      ├── Diet Preferences
      ├── Cuisine Preferences
      ├── Cost Preferences
      └── Other Supported Preferences
```

Internally:

```text
Diet / Cuisine / Cost / Other
             │
             ▼
            Tag
             │
             ▼
       UserPreference
```

Allergy selections use standardized `Allergen` entities rather than Tags.

```text
Allergy Selection
       │
       ▼
    Allergen
       │
       ▼
   UserAllergy
```

Users who skip onboarding may configure the same information later.

---

# 18. Recommendation Architecture

Recommendation logic belongs in the backend.

Both Guests and authenticated users use the same `RecommendationService`.

```text
Guest Ingredients ─────────────┐
                               │
                               ▼
                      RecommendationService
                               ▲
                               │
Saved User Inventory ──────────┘
```

The difference is where Ingredient data comes from.

---

# 19. Recommendation Input

The recommendation service receives normalized input.

Conceptually:

```text
RecommendationInput
│
├── ingredients
│
├── match_mode
│      ├── AVAILABLE_ONLY
│      └── PARTIAL_MATCH
│
├── allergen_ids
├── tag_ids
└── other supported filters
```

Ingredients should use canonical Ingredient identities whenever possible.

Tags represent standardized classifications and preferences.

Allergens remain structured separately from Tags.

---

# 20. Guest Recommendation Flow

```text
Guest
 │
 ▼
Select / Enter Ingredients
 │
 ▼
Ingredient Search / Resolution
 │
 ▼
Canonical Ingredient IDs
 │
 ├── Temporary Tag Filters
 ├── Temporary Allergen Filters
 └── Match Mode
 │
 ▼
POST /api/recommendations/
 │
 ▼
RecommendationService
 │
 ▼
Recipe Results
```

The Guest does not need a persistent inventory.

---

# 21. Registered User Recommendation Flow

An authenticated user may use saved application information.

```text
Saved Inventory ──────────────┐
                              │
Saved Allergies ──────────────┤
                              │
Saved Tag Preferences ────────┼──→ RecommendationInput
                              │
Current Search Filters ───────┘
```

The backend can derive saved data from the authenticated User.

React does not need to repeatedly send persistent User data when the backend can obtain it directly.

An authenticated user may still perform a temporary recommendation search using directly supplied Ingredient IDs without changing saved inventory.

---

# 22. AVAILABLE_ONLY Mode

In `AVAILABLE_ONLY` mode, every required Recipe Ingredient must be available.

Conceptually:

```text
Required Recipe Ingredients ⊆ Available Ingredients
```

Example:

```text
Available:
Egg
Cabbage
Soy Sauce
Kimchi

Recipe A:
Egg
Soy Sauce
→ Eligible

Recipe B:
Egg
Rice
→ Not Eligible
```

Optional RecipeIngredients do not determine eligibility.

---

# 23. PARTIAL_MATCH Mode

In `PARTIAL_MATCH` mode, a Recipe may be returned when at least one required Recipe Ingredient overlaps with the available Ingredients.

Conceptually:

```text
Required Recipe Ingredients ∩ Available Ingredients ≠ ∅
```

The RecommendationService identifies:

- Available Ingredients.
- Missing Ingredients.
- Optional missing Ingredients.
- Match score.

Example:

```text
Kimchi Fried Rice

Available:
✓ Kimchi
✓ Egg
✓ Soy Sauce

Missing:
✗ White Rice
✗ Green Onion
```

---

# 24. Recommendation Scoring

An initial match score may be calculated as:

```text
              Available Required Ingredients
Match Score = ------------------------------
                Total Required Ingredients
```

Example:

```text
Available Required Ingredients = 3
Total Required Ingredients     = 5

Match Score = 3 / 5 = 60%
```

The scoring algorithm may evolve later without changing the overall architecture.

React should display the score returned by the backend rather than independently recalculating the authoritative score.

---

# 25. Recommendation Result

Conceptually:

```text
RecommendationResult
│
├── recipe
├── match_score
├── available_ingredients
├── missing_ingredients
└── optional_missing_ingredients
```

Recommendation results do not need to be persisted initially.

They may be calculated dynamically for each request.

Persistent recommendation history or analytics may be introduced later if required.

---

# 26. Ingredient Resolution Architecture

User-entered Ingredient descriptions should be mapped to canonical Ingredients whenever possible.

```text
User Input
"Tyson Frozen Chicken Breast"
             │
             ▼
Ingredient Search / Resolution
             │
             ▼
Canonical Ingredient
"Chicken Breast"
             │
             ▼
RecommendationService
```

The system should not treat storage condition, brand, or packaging as separate Ingredients unless those distinctions materially affect recipe usage.

However, materially different foods should remain separate.

For example:

```text
Chicken Breast
Chicken Thigh
Ground Chicken
Whole Chicken
```

are separate canonical Ingredients.

---

# 27. Tag Architecture

Tags provide a common classification vocabulary.

```text
                       Tag
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
        DIET          CUISINE        COST
          │
          └────────────────────────── OTHER
```

Examples:

```text
Vegan       [DIET]
Halal       [DIET]
Korean      [CUISINE]
Vietnamese  [CUISINE]
Cheap       [COST]
Quick       [OTHER]
```

Tags are reused by both Recipes and User preferences.

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

This ensures that user preferences and Recipe classifications use the same standardized vocabulary.

---

# 28. Allergen Architecture

Allergens are separate from Tags.

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

Recipe allergen information can be determined through Recipe Ingredients.

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

This avoids relying solely on manually assigned labels such as `"Peanut-Free"` for allergy-related filtering.

---

# 29. Shopping List Architecture

Shopping-list generation uses canonical Ingredient information produced by recipe matching.

```text
Selected Recipe
      │
      ▼
RecipeIngredient
      │
      │ compare
      ▼
Available Ingredients
      │
      ▼
Missing Ingredients
      │
      ▼
ShoppingListService
```

For Guests:

```text
Missing Ingredients
       │
       ▼
Temporary Shopping List
```

For authenticated users:

```text
Missing Ingredients
       │
       ▼
ShoppingListService
       │
       ▼
ShoppingList
       │
       ▼
ShoppingListItem
       │
       ▼
Ingredient
```

This avoids duplicating Ingredient representations.

---

# 30. Review Architecture

Reviews belong to authenticated Users and Recipes.

```text
User
 │
 ▼
Review
 │
 ▼
Recipe
```

The backend derives the Review author from authenticated identity.

A normal user may modify or delete only their own Review.

Administrators may receive broader moderation permissions.

The initial design allows at most one active Review per User per Recipe.

---

# 31. Saved Recipe Architecture

Saved Recipes represent a relationship between an authenticated User and a Recipe.

```text
User
 │
 ▼
SavedRecipe
 │
 ▼
Recipe
```

The backend derives the User from authentication.

Guests cannot persist SavedRecipe relationships.

---

# 32. Media Architecture

Images should not be stored directly in PostgreSQL.

Conceptually:

```text
React
 │
 ▼
Django API
 │
 ├── PostgreSQL
 │      └── Media Reference
 │
 └── Object Storage
        └── Image File
```

Examples include:

- Recipe images.
- User profile images.

The database stores the information required to reference the media object.

Detailed AWS media infrastructure is defined in `aws-architecture.md`.

---

# 33. Database Architecture

PostgreSQL stores persistent relational application data.

Examples include:

```text
Users
Profiles
Ingredients
Inventories
Recipes
RecipeIngredients
SavedRecipes
Tags
UserPreferences
Allergens
UserAllergies
Reviews
ShoppingLists
ShoppingListItems
```

PostgreSQL does not store:

```text
Authentication passwords
Large image binaries
Temporary Guest state
Temporary recommendation results
```

Authentication passwords belong to Cognito.

Images belong to external media storage.

Temporary Guest and recommendation state may remain transient.

---

# 34. Stateless Backend Design

The backend should avoid unnecessary dependence on local server state.

Persistent application state belongs in external systems such as:

```text
PostgreSQL
Object Storage
Amazon Cognito
```

The Django container should not become the authoritative location for persistent application information.

Conceptually:

```text
             ┌── Django Instance A ──┐
Request ─────┤                       ├── PostgreSQL
             └── Django Instance B ──┘
                         │
                         └────────────── Object Storage
```

This allows future horizontal scaling.

The initial deployment may use only one Django backend instance.

---

# 35. Scalability Architecture

The initial application does not require a distributed microservice architecture.

Instead, it should be designed so that future scaling does not require rewriting the entire system.

Initial deployment:

```text
Client
  │
  ▼
Frontend
  │
  ▼
Single Django Backend Instance
  │
  ▼
PostgreSQL
```

Future scaling may introduce:

```text
Clients
   │
   ▼
Load Balancer
   │
   ├── Django Instance A
   ├── Django Instance B
   └── Django Instance C
              │
              ▼
          PostgreSQL
```

This is possible because persistent application state is external to individual backend instances.

---

# 36. Docker Architecture

The Django backend is containerized.

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

The container contains application runtime code and dependencies.

It does not contain the authoritative persistent database or media files.

```text
Backend Container
      │
      ├── PostgreSQL
      ├── Object Storage
      └── Cognito
```

This provides a consistent runtime between development and cloud deployment.

---

# 37. Development Architecture

During local development, the application may run as:

```text
Developer Machine
│
├── React Development Server
│
└── Django Backend
       │
       └── Development Database
```

Docker may be used to provide a consistent backend runtime.

The local environment should remain sufficiently similar to cloud deployment to reduce environment-specific problems.

---

# 38. Production Architecture

At a high level, production follows:

```text
Users
  │
  ▼
Frontend Hosting
  │
  ▼
Django Backend
  │
  ├── PostgreSQL Database
  ├── Media Storage
  └── Amazon Cognito
```

The exact AWS services, network configuration, deployment process, monitoring, and scaling strategy are defined in `aws-architecture.md`.

---

# 39. Security Boundaries

The system contains several important security boundaries.

## 39.1 Browser Boundary

React runs in the user's browser and must not be trusted with authoritative security decisions.

---

## 39.2 Authentication Boundary

Amazon Cognito establishes authenticated identity.

---

## 39.3 Authorization Boundary

Django determines what authenticated users are allowed to access or modify.

---

## 39.4 Persistence Boundary

Persistent application data is stored in controlled backend systems rather than trusted directly from client state.

---

## 39.5 Media Boundary

Uploaded files should be handled through controlled application/storage mechanisms.

The database should store references rather than arbitrary binary data.

---

# 40. Testing Architecture

Testing occurs at multiple layers.

```text
Frontend Tests
      │
      ▼
API Tests
      │
      ▼
Service / Business Logic Tests
      │
      ▼
Model / Database Tests
```

Backend tests should cover:

- Authentication integration.
- Authorization.
- Resource ownership.
- Ingredient behavior.
- Tag behavior.
- Allergen behavior.
- Inventory.
- Recipes.
- Recommendation modes.
- Recommendation scoring.
- Saved Recipes.
- Reviews.
- Shopping Lists.

Postman may be used for manual API testing.

Automated Django/DRF tests should verify important backend behavior.

GitHub Actions may run automated tests during integration.

---

# 41. Key End-to-End Flow: Guest Recommendation

```text
Guest
  │
  ▼
React Ingredient Selection
  │
  ▼
Canonical Ingredient IDs
  │
  ├── Tag Filters
  ├── Allergen Filters
  └── Match Mode
  │
  ▼
Django Recommendation API
  │
  ▼
RecommendationService
  │
  ▼
RecipeIngredient / Ingredient / Tag / Allergen Data
  │
  ▼
Recommendation Results
  │
  ▼
React
```

No persistent User account is required.

---

# 42. Key End-to-End Flow: Registered User Recommendation

```text
Registered User
      │
      ▼
Amazon Cognito
      │
      ▼
Authenticated Request
      │
      ▼
Django
      │
      ▼
Application User
      │
      ├── Saved Inventory
      ├── Saved Tag Preferences
      └── Saved Allergies
      │
      ▼
RecommendationService
      │
      ▼
Recipe Results
      │
      ▼
React
```

The same RecommendationService is used for Guest and authenticated workflows.

---

# 43. Key End-to-End Flow: Recipe Creation

```text
Registered User
      │
      ▼
Amazon Cognito
      │
      ▼
React Recipe Form
      │
      ├── Recipe Information
      ├── Canonical Ingredient IDs
      └── Tag IDs
      │
      ▼
POST /api/recipes/
      │
      ▼
Django Authorization
      │
      ▼
Recipe.owner = Authenticated User
      │
      ▼
Recipe
 ├── RecipeIngredient
 └── Tag
```

The frontend does not submit authoritative ownership information.

---

# 44. Key End-to-End Flow: Shopping List

```text
Recipe
  │
  ▼
RecipeIngredient
  │
  │ compare against
  ▼
Available Ingredients
  │
  ▼
Missing Ingredients
  │
  ▼
ShoppingListService
  │
  ├── Guest → Temporary List
  │
  └── User  → Persistent ShoppingList
```

All ShoppingListItems continue to reference canonical Ingredients.

---

# 45. Core Architectural Rules

The implementation should follow these rules:

1. React shall not access PostgreSQL directly.
2. Cognito handles authentication identity.
3. Django handles authorization and ownership.
4. Client-provided ownership information shall not be trusted.
5. Persistent domain relationships should use canonical IDs.
6. Ingredient is the shared food representation across application domains.
7. Tags classify Recipes and represent persistent User preferences.
8. Allergens remain structured separately from Tags.
9. Guest and Registered User recommendation logic shall remain shared.
10. Business logic belongs in backend services rather than React.
11. Persistent state shall not depend on a specific Django instance.
12. Media binaries shall remain outside PostgreSQL.
13. The initial architecture should remain simple enough for the team to implement and maintain.
14. Future scalability should be supported without prematurely introducing microservices.

---

# 46. Architecture Summary

The overall system can be summarized as:

```text
                         User
                          │
                          ▼
                     React Frontend
                          │
                          │ REST / JSON
                          ▼
                    Django REST API
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
   Authorization     Service Layer     Cognito
          │               │          Authentication
          │               │
          │        ┌──────┼─────────┐
          │        │      │         │
          ▼        ▼      ▼         ▼
       User   Ingredients Recipes Recommendations
          │        │      │         │
          │        └──────┼─────────┘
          │               │
          ▼               ▼
      PostgreSQL      Shopping Logic
                          │
                          ▼
                    Media / Storage
```

The architecture intentionally separates:

```text
Authentication
      ↓
Amazon Cognito

Authorization + Business Logic
      ↓
Django

Persistent Relational Data
      ↓
PostgreSQL

Media
      ↓
Object Storage

Presentation
      ↓
React
```

This separation provides a clear, maintainable foundation for the initial implementation while supporting future scaling.

---

# 47. Related Documentation

```text
requirements.md
    ↓
What must the application do?

database-design.md
    ↓
How is persistent application data represented?

api-design.md
    ↓
How does React interact with Django?

system-design.md
    ↓
How do application components work together?

aws-architecture.md
    ↓
How is the system deployed in AWS?
```
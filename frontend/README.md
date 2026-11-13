# Frontend

React frontend for the Recipe Suggestion App.

The frontend communicates with the Django backend through the documented REST API.

For complete system requirements and architecture, see the documentation under [`../docs/`](../docs/).

---

## Frontend Structure

The frontend follows a modular, component-based architecture with separation between UI, application features, domain models, and API communication.

```text
frontend/
├── public/
│
├── src/
│   ├── app/                    # Application-wide configuration
│   │   └── router/             # Routing configuration
│   │
│   ├── components/             # Shared reusable UI components
│   │   ├── common/
│   │   └── layout/
│   │
│   ├── features/               # Feature-specific code
│   │   ├── auth/
│   │   ├── ingredients/
│   │   ├── inventory/
│   │   ├── recipes/
│   │   ├── recommendations/
│   │   ├── profile/
│   │   ├── reviews/
│   │   └── shopping/
│   │
│   ├── models/                 # Frontend domain/data models
│   │
│   ├── services/               # External/API communication
│   │   └── api/
│   │
│   ├── pages/                  # Page-level components
│   │
│   ├── App.jsx
│   └── main.jsx
│
├── .env.example
├── eslint.config.js
├── package.json
├── package-lock.json
└── vite.config.js
```

Some directories may be created incrementally as their features are implemented.

---

## Responsibilities

### `pages/`

Page-level application screens.

Examples:

```text
HomePage
RecipePage
RecipeSearchPage
DashboardPage
ProfilePage
SavedRecipesPage
ShoppingListPage
LoginPage
```

Pages should compose reusable components and feature functionality rather than contain large amounts of business logic.

---

### `components/`

Reusable UI components shared across the application.

Examples:

```text
Navbar
RecipeCard
IngredientInput
SearchBar
LoadingSpinner
TagSelector
AllergenSelector
```

Shared components should remain presentation-focused where practical.

Feature-specific behavior should remain inside the corresponding feature.

---

### `features/`

Feature-specific frontend functionality.

For example:

```text
features/
└── ingredients/
    ├── components/
    ├── hooks/
    └── utils/
```

Code that is only relevant to one feature should generally remain inside that feature.

Major frontend features include:

```text
auth
ingredients
inventory
recipes
recommendations
profile
reviews
shopping
```

---

### `models/`

Frontend representations of application/domain data.

Examples include:

```text
Recipe
Ingredient
Tag
Allergen
UserProfile
InventoryItem
Review
ShoppingList
ShoppingListItem
```

These representations should remain consistent with the backend API contract.

The frontend should not invent a conflicting domain model.

---

### `services/`

Handles communication with the backend and other external services.

The frontend uses a **centralized API client with domain-specific service files**.

Conceptually:

```text
services/api/
├── apiClient.js
├── ingredientService.js
├── recipeService.js
├── inventoryService.js
├── recommendationService.js
├── userService.js
├── reviewService.js
└── shoppingListService.js
```

Additional domain services may be introduced as required.

For example, Tag and Allergen reference endpoints may be handled by an appropriate existing service or dedicated service when useful.

`apiClient.js` is responsible for shared HTTP behavior such as:

- API base URL.
- HTTP methods.
- Common headers.
- JSON serialization/deserialization.
- Common error handling.
- Authentication headers when Cognito is integrated.

Feature/domain services are responsible for defining calls to their corresponding backend APIs.

For example:

```text
Component
    ↓
ingredientService
    ↓
apiClient
    ↓
Django REST API
```

Components should **not call `fetch()` directly**.

Domain services should use the shared `apiClient` rather than implementing their own HTTP configuration.

---

## Frontend Data Flow

The general frontend flow should be:

```text
Page / Component
       │
       ▼
Feature / Service
       │
       ▼
API Client
       │
       ▼
Django REST API
```

For example:

```text
RecipeSearchPage
       │
       ▼
recommendationService
       │
       ▼
POST /api/recommendations/
       │
       ▼
Django Backend
       │
       ▼
Recommendation Results
       │
       ▼
React UI
```

Core recommendation logic belongs in the backend.

---

## Canonical Application Data

The frontend should use the same standardized domain concepts defined by the backend.

### Ingredient

Represents a canonical food Ingredient.

Examples:

```text
Chicken Breast
Egg
White Rice
Soy Sauce
```

Frontend features should use canonical Ingredient IDs when communicating with APIs where required.

---

### Tag

Represents a standardized Recipe classification or User preference.

Initial Tag types include:

```text
DIET
CUISINE
COST
OTHER
```

Examples:

```text
Halal       [DIET]
Vegan       [DIET]
Vietnamese  [CUISINE]
Korean      [CUISINE]
Cheap       [COST]
Quick       [OTHER]
```

Persistent User preferences use Tag IDs.

The frontend should not create separate incompatible free-text systems for diet, cuisine, and cost preferences.

---

### Allergen

Represents structured allergy information.

Examples:

```text
Peanut
Milk
Soy
Shellfish
```

Allergens are separate from Tags.

The frontend may allow users to select Allergens, but authoritative allergy filtering belongs to the backend.

---

## Guest and Registered User Behavior

Guests and Registered Users share the same core recipe-discovery experience.

```text
Guest
  │
  ├── Enter temporary Ingredients
  ├── Select temporary Tag filters
  ├── Select temporary Allergen filters
  ├── Search Recipes
  ├── Receive recommendations
  ├── View Recipes
  └── Generate temporary shopping lists
```

Registered Users receive all Guest functionality plus persistent features.

```text
Registered User
  │
  ├── All Guest functionality
  ├── Saved inventory
  ├── Saved Tag preferences
  ├── Saved allergies
  ├── Saved Recipes
  ├── Reviews
  ├── Persistent ShoppingLists
  └── Profile
```

Administrators should also retain access to the normal Registered User interface.

Administrative functionality is additional rather than a separate user experience.

---

## Recommendation UI

The frontend supports two recommendation modes:

```text
AVAILABLE_ONLY
PARTIAL_MATCH
```

Guest requests may use temporary data:

```text
Temporary Ingredient IDs
Temporary Tag IDs
Temporary Allergen IDs
Match Mode
```

Authenticated users may use saved inventory and saved preferences through backend functionality.

The frontend should display recommendation information returned by the backend, such as:

```text
Recipe
Match Score
Available Ingredients
Missing Ingredients
Optional Missing Ingredients
```

The frontend must not independently calculate the authoritative match score or determine authoritative Recipe eligibility.

---

## Recipe UI

Recipe views may display:

```text
Name
Description
Preparation Time
Cooking Time
Ingredients
Tags
Instructions
Image
Average Rating
Reviews
```

Recipe Ingredients should correspond to canonical backend Ingredients.

Recipe classifications should correspond to backend Tags.

Authenticated users may create Recipes.

Where supported:

```text
Recipe Create
    → Registered User

Recipe Update/Delete
    → Owner or Administrator
```

The frontend may hide unavailable actions for usability, but Django remains responsible for enforcing ownership and permissions.

---

## Profile and Preferences

Profile functionality may allow authenticated users to manage:

```text
Display Name
Profile Image
Tag Preferences
Allergies
```

Persistent preference updates should use canonical Tag IDs.

Example conceptually:

```json
{
  "tag_ids": [4, 8, 12]
}
```

Allergy updates should use canonical Allergen IDs.

Example conceptually:

```json
{
  "allergen_ids": [1, 4]
}
```

The exact API contract is defined in `../docs/api-design.md`.

---

## Inventory

Persistent inventory belongs to authenticated users.

The frontend should submit canonical Ingredient IDs.

Conceptually:

```json
{
  "ingredient_id": 3
}
```

The frontend does not submit an authoritative User ID.

Django derives the inventory owner from authentication.

Guest Ingredient selections remain temporary and should not be treated as persistent inventory.

---

## Reviews

Guests may read Recipe Reviews.

Authenticated users may create Reviews.

Users may modify or delete their own Reviews where permitted.

The frontend should not submit an authoritative Review author ID.

Django derives the Review author from authentication.

---

## Shopping Lists

Guests may generate temporary shopping lists from missing Recipe Ingredients.

Authenticated users may maintain persistent ShoppingLists.

ShoppingListItems should use canonical Ingredient IDs when communicating with the backend.

The frontend should not duplicate shopping-list ownership logic.

---

## Authentication

Amazon Cognito is the authentication provider.

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
 ▼
Authentication Token
 │
 ▼
React API Service
 │
 ▼
Django REST API
```

Cognito establishes identity.

Django determines application permissions and resource ownership.

Authentication-related functionality should remain inside the appropriate authentication feature/service.

Do not build a competing authentication system inside React.

---

## Authorization and Ownership

React is not an authorization boundary.

The frontend may use authentication and ownership information to decide which controls to display, but Django makes the authoritative permission decision.

For example:

```text
User owns Recipe
      │
      ▼
React may show Edit/Delete controls
      │
      ▼
PATCH / DELETE request
      │
      ▼
Django verifies ownership
```

The frontend should not attempt to assign resource ownership by submitting fields such as:

```text
user_id
owner_id
review_author_id
```

when the backend can derive ownership from authentication.

---

## API Usage

The frontend communicates with the Django backend through the documented REST API.

See:

```text
../docs/api-design.md
```

Do not hardcode backend URLs throughout individual components.

Use an environment variable and the shared API service layer.

For example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Then API services can build requests from the configured base URL.

Important API domains include:

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

The API documentation remains the source of truth for request and response contracts.

---

## Development Rules

When contributing to the frontend:

1. Keep page components focused on page composition.
2. Create reusable components when UI is shared.
3. Keep feature-specific code inside the appropriate feature.
4. Use the shared API service layer for backend communication.
5. Keep authoritative backend business rules out of React.
6. Follow the API contract in `docs/api-design.md`.
7. Do not duplicate the same API request logic across components.
8. Keep authentication-related functionality inside the authentication feature/service.
9. Do not hardcode secrets or production URLs.
10. Run the linter before submitting changes.
11. Avoid introducing unnecessary dependencies.
12. Discuss major architecture changes before implementing them.
13. Use `apiClient.js` for all backend HTTP communication.
14. Create domain-specific API services rather than placing all API endpoints in one file.
15. Use canonical Ingredient, Tag, and Allergen IDs according to the API contract.
16. Do not treat frontend permission checks as authoritative security.
17. Do not submit ownership identifiers when ownership is derived from authentication.
18. Keep Guest and Registered User recommendation UI compatible with the same backend Recommendation API.

---

## Do NOT

Do not:

- Implement Recipe recommendation algorithms in React.
- Recalculate authoritative recommendation scores in React.
- Directly access the database.
- Duplicate backend validation as the authoritative validation source.
- Hardcode API URLs across components.
- Put all application logic inside `App.jsx`.
- Create one massive component containing an entire feature.
- Implement an alternative authentication system.
- Add major libraries/frameworks without discussing them with the team.
- Modify unrelated features while completing an assigned task.
- Commit `.env`, `node_modules/`, or generated build files.
- Push feature development directly to `main`.
- Call `fetch()` directly from React components.
- Create a second shared API client.
- Put every backend endpoint into `apiClient.js`.
- Create conflicting free-text preference systems when standardized Tags exist.
- Treat Allergens and Tags as the same concept.
- Trust client-side ownership checks as security.

Client-side validation may still be used to improve user experience, but the backend remains responsible for authoritative validation, authorization, ownership, and business rules.

---

## Local Development

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The Vite development server will normally be available at:

```text
http://localhost:5173/
```

Run ESLint:

```bash
npm run lint
```

Build the production frontend:

```bash
npm run build
```

---

## Environment Variables

Local environment variables should not be committed.

Use:

```text
frontend/.env
```

A committed `.env.example` should document required variables without containing secrets.

Example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### Cognito sign-in configuration

Authentication uses Cognito managed login (Hosted UI) with the OAuth 2.0
Authorization Code flow + PKCE. No extra npm dependency is used: see
`src/features/auth/`.

| Variable | Required | Description |
| --- | --- | --- |
| `VITE_COGNITO_DOMAIN` | Yes | Cognito domain, e.g. `https://<prefix>.auth.<region>.amazoncognito.com` |
| `VITE_COGNITO_CLIENT_ID` | Yes | Public app client ID (no client secret) |
| `VITE_COGNITO_REDIRECT_URI` | No | Defaults to `<origin>/auth/callback` |
| `VITE_COGNITO_LOGOUT_URI` | No | Defaults to `<origin>/` |
| `VITE_COGNITO_SCOPES` | No | Defaults to `openid email profile` |
| `VITE_COGNITO_GOOGLE_PROVIDER` | No | Identity provider name in the User Pool, defaults to `Google` |

Cognito app client settings (project manager / AWS console):

- App type: public client, **no client secret**.
- OAuth grant: Authorization code grant. Scopes: `openid`, `email`, `profile`.
- Identity providers: Cognito user pool and Google.
- Allowed callback URLs: `http://localhost:5173/auth/callback` and `https://<cloudfront-domain>/auth/callback`.
- Allowed sign-out URLs: `http://localhost:5173/` and `https://<cloudfront-domain>/`.

Production routing: the CloudFront SPA rewrite function serves `index.html`
for extensionless, non-`/api` paths, so `/auth/callback?code=...` reaches the
React router with its query string intact. No CloudFront change is needed.

How it works:

- `/login` offers Continue with Google (`identity_provider=Google`), email sign-in and sign-up (`/signup`).
- `/auth/callback` validates the one-time `state`, exchanges the code with the PKCE verifier, removes the code from the URL and returns to the original page (same-origin paths only).
- Tokens live in `sessionStorage` (survive refresh, cleared when the tab closes) and are never placed in URLs or logs.
- `apiClient` attaches `Authorization: Bearer <access token>` to API calls, refreshes the token before expiry, and on a `401` refreshes once and retries. If the session can't be refreshed it is cleared, the user sees a "session expired" message, and public requests are retried as a guest.
- After sign-in the app calls `GET /api/auth/me/` (backend issue #68) for the current user.
- `/dashboard` and `/profile` are protected client-side; recipes stay public. Django remains the authorization boundary.
- Sign out clears local state and redirects to Cognito `/logout`.

Only configuration intended to be publicly available to browser code should use Vite frontend environment variables.

Sensitive backend secrets must not be placed in the React application.

---

## Production Deployment

The production React application is built into static files.

Conceptually:

```text
React Source
     │
     ▼
npm run build
     │
     ▼
Static Build
     │
     ▼
Amazon S3
     │
     ▼
Amazon CloudFront
     │
     ▼
Users
```

AWS deployment details are documented in:

```text
../docs/aws-architecture.md
```

---

## Before Submitting

Before opening a Pull Request:

```bash
npm run lint
npm run build
```

Verify that the application still starts correctly:

```bash
npm run dev
```

Verify that:

- Relevant pages still load.
- API calls use the shared service layer.
- No environment secrets were committed.
- No unrelated feature was changed accidentally.
- New frontend behavior follows the documented API contract.

Then open a Pull Request into `main`.

**Do not push feature implementation directly to `main`.**

---

## Related Documentation

```text
../README.md
    High-level project overview

../docs/requirements.md
    Functional and non-functional requirements

../docs/database-design.md
    Persistent models and relationships

../docs/api-design.md
    REST API contract

../docs/system-design.md
    Application architecture

../docs/aws-architecture.md
    AWS deployment architecture

../CONTRIBUTING.md
    Team development guidelines
```

If implementation requires changing an established API or architecture decision, discuss and update the relevant documentation rather than introducing a conflicting frontend implementation.
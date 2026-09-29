# Frontend

React frontend for the Recipe Suggestion App.

The frontend communicates with the Django backend through the REST API.

For complete system requirements and architecture, see the documentation under [`../docs/`](../docs/).

---

## Frontend Structure

The frontend follows a modular, component-based architecture with separation between UI, application features, domain models, and API communication.

```text
frontend/
├── public/
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
│   │   └── profile/
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
LoginPage
```

Pages should compose reusable components and feature functionality rather than contain large amounts of business logic.

### `components/`

Reusable UI components shared across the application.

Examples:

```text
Navbar
RecipeCard
IngredientInput
SearchBar
LoadingSpinner
```

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

### `models/`

Frontend representations of application/domain data.

Examples include:

```text
Recipe
Ingredient
UserProfile
InventoryItem
```

These should remain consistent with the backend API contract.

### `services/`

Communication with the backend and other external services.

For example:

```text
services/api/
├── apiClient.js
├── ingredientService.js
├── recipeService.js
├── inventoryService.js
└── recommendationService.js
```

React components should use these services instead of duplicating API request code throughout the application.

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
RecommendationService
       │
       ▼
POST /api/recommendations/
       │
       ▼
Django Backend
```

Core recommendation logic belongs in the backend.

---

## Guest and Registered User Behavior

Guests and Registered Users share the same core recipe discovery experience.

```text
Guest
  │
  ├── Enter temporary ingredients
  ├── Search recipes
  ├── Receive recommendations
  └── View recipes


Registered User
  │
  ├── All Guest functionality
  ├── Saved inventory
  ├── Saved preferences
  ├── Saved recipes
  └── Personalized experience
```

Administrators should also retain access to the normal Registered User interface.

---

## API Usage

The frontend communicates with the Django backend through the documented REST API.

See:

`../docs/api-design.md`

Do not hardcode backend URLs throughout individual components.

Use an environment variable and the shared API service layer.

For example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then API services can build requests from the configured base URL.

---

## Development Rules

When contributing to the frontend:

1. Keep page components focused on page composition.
2. Create reusable components when UI is shared.
3. Keep feature-specific code inside the appropriate feature.
4. Use the shared API service layer for backend communication.
5. Keep backend business rules out of React.
6. Follow the API contract in `docs/api-design.md`.
7. Do not duplicate the same API request logic across components.
8. Keep authentication-related functionality inside the authentication feature/service.
9. Do not hardcode secrets or production URLs.
10. Run the linter before submitting changes.
11. Avoid introducing unnecessary dependencies.
12. Discuss major architecture changes before implementing them.

---

## Do NOT

Do not:

- Implement recipe recommendation algorithms in React.
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

Client-side validation may still be used to improve user experience, but the backend remains responsible for authoritative validation and business rules.

---

## Authentication

Amazon Cognito is the planned authentication provider.

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

Authentication integration will be implemented separately.

Do not build a competing authentication system inside React.

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
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Additional Cognito/AWS configuration can be added when authentication is implemented.

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

Then open a Pull Request into `main`.

**Do not push feature implementation directly to `main`.**

---

## Related Documentation

```text
../README.md
    High-level project overview

../docs/requirements.md
    Functional and non-functional requirements

../docs/system-design.md
    Application architecture

../docs/api-design.md
    REST API contract

../docs/aws-architecture.md
    AWS deployment architecture

../CONTRIBUTING.md
    Team development guidelines
```
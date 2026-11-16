# Frontend — Recipe Suggestion App

The frontend of the Recipe Suggestion App is built using **React, Vite, and React Router**. It provides a responsive web interface for discovering recipes, managing ingredients, and accessing personalized features.

The application communicates with the Django REST Framework backend through REST APIs and is deployed using Amazon S3 and CloudFront.

## Technology Stack

| Component | Technology |
|---|---|
| Framework | React |
| Build Tool | Vite |
| Routing | React Router |
| Authentication | Amazon Cognito with Google Sign-In |
| API Communication | REST API |
| Hosting | Amazon S3 |
| Content Delivery | Amazon CloudFront |
| Code Quality | ESLint |

## Frontend Structure

The frontend follows a component-based architecture, separating reusable UI components, application features, and backend API communication.

```text
frontend/
├── public/                  # Public assets
├── src/
│   ├── app/                 # Application configuration and routing
│   ├── components/          # Shared UI components
│   ├── features/            # Feature-specific functionality
│   │   ├── auth/
│   │   ├── ingredients/
│   │   ├── inventory/
│   │   ├── recipes/
│   │   ├── recommendations/
│   │   └── profile/
│   ├── models/              # Application data models
│   ├── services/            # Backend API communication
│   ├── pages/               # Application pages
│   ├── App.jsx
│   └── main.jsx
├── package.json
├── vite.config.js
└── eslint.config.js
```

## Implemented Features

- **Recipe Discovery:** Browse, search, filter, and view recipes with ingredients and cooking instructions.
- **Ingredient-Based Recommendations:** Discover recipes based on available ingredients.
- **Personal Inventory:** Manage saved ingredients for recipe recommendations.
- **User Dashboard:** Access personalized features after signing in.
- **Profile and Preferences:** Manage display name, dietary preferences, and allergies.
- **Saved Recipes:** Save and view favorite recipes.
- **Recipe Submission:** Submit new recipes with ingredients, instructions, and images.
- **Authentication:** Sign in and sign out using Amazon Cognito, including Google Sign-In.

Public recipe browsing is available to guests. Personal inventories, saved recipes, profile management, and recipe submission require authentication.

## Authentication

The frontend integrates with **Amazon Cognito User Pools** using the OAuth 2.0 Authorization Code flow with PKCE.

The authentication process follows these steps:

1. The user initiates sign-in through Cognito, including Google Sign-In.
2. Cognito redirects the user to `/auth/callback` after authentication.
3. React exchanges the authorization code for tokens using PKCE.
4. The frontend sends the Cognito access token with authenticated API requests.
5. Django validates the token and enforces application permissions.

Authenticated API requests include:

```http
Authorization: Bearer <access_token>
```

Authentication tokens are stored in `sessionStorage`. The frontend handles token refresh, session expiration, and sign-out.

Protected pages are restricted to authenticated users, while the backend remains responsible for enforcing authorization.

## API Integration

The frontend communicates with the backend through a shared API client and feature-specific services.

The API base URL is configured using:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Major API integrations include recipe browsing, recommendations, ingredients, inventory management, saved recipes, user profiles, and authentication.

## Local Development

### Prerequisites

- Node.js and npm
- A running Django backend

### 1. Install dependencies

From the `frontend/` directory:

```bash
npm install
```

### 2. Configure environment variables

Create a `.env` file in the `frontend/` directory.

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api

VITE_COGNITO_DOMAIN=https://<domain>.auth.<region>.amazoncognito.com
VITE_COGNITO_CLIENT_ID=<app-client-id>
VITE_COGNITO_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_COGNITO_LOGOUT_URI=http://localhost:5173/
```

The Cognito domain, client ID, and callback URLs must match the configured Cognito User Pool application client.

Only public configuration values should be included in frontend environment variables. Do not expose backend secrets.

### 3. Start the development server

```bash
npm run dev
```

The application is available at:

```text
http://localhost:5173/
```

### 4. Run validation commands

```bash
npm run lint
npm run build
```

These commands run ESLint and generate the production build.

## Production Deployment

The production frontend is built using Vite and deployed as static files to a private Amazon S3 bucket.

Amazon CloudFront provides the public entry point for the application.

- **Amazon S3:** Stores the compiled React frontend.
- **CloudFront Origin Access Control (OAC):** Restricts direct access to the frontend bucket.
- **CloudFront VPC Origin:** Connects API requests to the internal Application Load Balancer.
- **SPA Routing:** Rewrites frontend routes to `index.html` to support React Router.

CloudFront serves frontend assets from S3 and forwards `/api/*` requests to the Django backend through the internal ALB.

The frontend S3 bucket does not use public static website hosting.

## Documentation

For additional information, refer to the project documentation in [`../docs/`](../docs/) and the [main project README](../README.md).
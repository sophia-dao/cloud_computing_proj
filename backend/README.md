# Backend — Recipe Suggestion App

The backend of the Recipe Suggestion App is built using **Django and Django REST Framework (DRF)**. It provides REST APIs for recipe management, ingredient inventories, recommendations, user preferences, and authentication.

The application is containerized using Docker and deployed on AWS EC2, with Amazon RDS PostgreSQL for persistent data storage and Amazon S3 for recipe images.

## Technology Stack

| Component | Technology |
|---|---|
| Framework | Django, Django REST Framework |
| Language | Python |
| Database | PostgreSQL (Amazon RDS in production) |
| Authentication | Amazon Cognito with Google Sign-In |
| Containerization | Docker, Gunicorn |
| Hosting | Amazon EC2 Auto Scaling |
| Load Balancing | Internal Application Load Balancer |
| Media Storage | Amazon S3 |
| Container Registry | Amazon ECR |
| Testing | Django Test Framework |

## Backend Structure

The backend follows a modular architecture, with functionality separated into Django applications.

```text
backend/
├── apps/
│   ├── users/             # User profiles, preferences, allergies, authentication
│   ├── ingredients/       # Ingredient and allergen data
│   ├── inventory/         # Personal ingredient inventories
│   ├── recipes/           # Recipes, submissions, saved recipes
│   └── recommendations/   # Ingredient-based recipe matching
├── config/                # Django configuration
├── tests/                 # Integration and API tests
├── manage.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
└── .env.example
```

Each Django application contains its own models, serializers, views, and related business logic as needed.

## Implemented Features

- **Recipe Management:** Browse, search, filter, and view recipes, including ingredients and cooking instructions.
- **Recipe Submission:** Authenticated users can submit recipes with ingredients, instructions, and images.
- **Saved Recipes:** Registered users can save and manage their favorite recipes.
- **Ingredient Inventory:** Registered users can maintain personal inventories of available ingredients.
- **Recipe Recommendations:** Match recipes against available ingredients using `AVAILABLE_ONLY` and `PARTIAL_MATCH` modes.
- **User Preferences:** Manage dietary preferences and allergies, with automatic preference filtering for authenticated users.
- **Authentication:** Validate Amazon Cognito access tokens and enforce application-level permissions.

The initial production database was populated using TheMealDB API and contains 100 recipes with associated images.

## Authentication and Authorization

Authentication is handled through **Amazon Cognito User Pools**, with Google Sign-In supported through Cognito's hosted authentication flow.

The frontend sends a Cognito access token with authenticated API requests:

```http
Authorization: Bearer <access_token>
```

The backend validates the token's signature, issuer, expiration, token type, and application client ID.

Authenticated Cognito identities are mapped to local Django user records using the Cognito issuer and subject (`sub`).

Django REST Framework enforces permissions for protected resources, including personal inventories, saved recipes, user preferences, and recipe submissions.

The API also provides `/api/auth/me/` to retrieve the authenticated user's application profile.

## API

The backend exposes REST endpoints under the `/api/` prefix.

| Endpoint | Purpose |
|---|---|
| `/api/recipes/` | Recipe browsing, filtering, and submission |
| `/api/ingredients/` | Ingredient lookup |
| `/api/tags/` | Recipe tags and preference categories |
| `/api/inventory/` | Personal ingredient inventory |
| `/api/recommendations/` | Ingredient-based recipe recommendations |
| `/api/saved-recipes/` | Saved recipe management |
| `/api/users/me/` | User profile management |
| `/api/auth/me/` | Authenticated user information |

Additional endpoints support user preferences, allergies, and recipe details.

## Local Development

### Prerequisites

- Python and pip
- Docker Desktop with Docker Compose

### 1. Configure environment variables

From the `backend/` directory:

```bash
cp .env.example .env
```

Update `.env` with the appropriate Django, database, and authentication settings.

### 2. Set up Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start PostgreSQL

```bash
docker compose up -d db
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Run the backend

```bash
python manage.py runserver
```

The local backend runs at `http://127.0.0.1:8000/` by default.

Alternatively, run both Django and PostgreSQL using Docker Compose:

```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

Ensure the database host is configured appropriately for local Python execution (`127.0.0.1`) or Docker Compose (`db`).

## Testing

The backend includes automated unit and API tests covering recipe management, ingredients, recommendations, user authentication, permissions, and other application functionality.

Run the test suite:

```bash
python manage.py test
```

The final backend test run completed with **359 tests passing and 1 skipped**.

API load testing was also performed using ApacheBench with concurrency levels of 10, 50, and 100 to evaluate backend performance.

## Production Deployment

The production backend is deployed using Docker containers on Amazon EC2 instances within private application subnets.

- **EC2 Auto Scaling Group:** Maintains two backend instances across two Availability Zones, with capacity to scale to three.
- **Internal Application Load Balancer:** Distributes API requests across healthy backend instances.
- **Amazon CloudFront:** Routes `/api/*` requests to the internal ALB through a VPC origin.
- **Amazon RDS:** Hosts the production PostgreSQL database.
- **Amazon S3:** Stores uploaded recipe images privately.
- **Amazon ECR:** Stores Docker images used by EC2 instances.
- **AWS CloudFormation:** Provisions and manages the infrastructure.

AWS Systems Manager provides administrative access to private EC2 instances without requiring public IP addresses.

## Documentation

For additional information, refer to the project documentation in [`../docs/`](../docs/) and the [main project README](../README.md).
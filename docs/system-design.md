# System Design — Recipe Suggestion App

## 1. Overview

The Recipe Suggestion App is a cloud-based web application that helps users discover recipes based on available ingredients and personal preferences.

The application follows a client-server architecture consisting of a React frontend, Django REST Framework backend, and PostgreSQL database. It is deployed on Amazon Web Services (AWS), with Amazon Cognito providing user authentication and Amazon S3 storing recipe images.

The backend uses a **modular monolith architecture**, separating application functionality into Django modules while maintaining a single backend deployment.

This design provides a maintainable application structure while supporting horizontal scaling through AWS infrastructure.

## 2. High-Level Architecture

The application consists of the following major components:

| Component | Responsibility |
|---|---|
| React Frontend | User interface, navigation, forms, and API communication |
| Django REST Framework | REST APIs, business logic, validation, and authorization |
| PostgreSQL | Persistent relational application data |
| Amazon Cognito | User authentication and Google Sign-In |
| Amazon S3 | Frontend static files and recipe image storage |
| AWS Infrastructure | Hosting, networking, load balancing, and scaling |

### Application Flow

```text
User
 │
 ▼
Amazon CloudFront
 │
 ├── React Frontend (Private S3)
 │
 └── /api/* → Internal Application Load Balancer
                   │
                   ▼
             Django REST API
             (EC2 Auto Scaling)
                   │
          ┌────────┴─────────┐
          │                  │
          ▼                  ▼
    PostgreSQL RDS      S3 Media Storage

Authentication: Amazon Cognito + Google Sign-In
```

CloudFront serves the frontend from a private S3 bucket and routes API requests to the backend through a VPC origin.

The Django backend handles application logic and communicates with PostgreSQL and S3 for persistent storage.

Detailed AWS infrastructure and networking are documented in [AWS Architecture](aws-architecture.md).

## 3. Backend Architecture

The backend is developed using Django and Django REST Framework. It follows a modular architecture with functionality separated into five Django applications.

| Django App | Responsibility |
|---|---|
| `users` | User profiles, Cognito identity mapping, preferences, allergies, and permissions |
| `ingredients` | Ingredient records, tags, and allergen data |
| `recipes` | Recipe management, submissions, recipe ingredients, and saved recipes |
| `inventory` | Personal ingredient inventory management |
| `recommendations` | Ingredient-based recipe matching and filtering |

Each module contains its own models, serializers, views, and business logic as appropriate.

The backend is responsible for request validation, application authorization, resource ownership, recommendation calculations, and database operations.

### Design Principles

- **Modularity:** Application domains are organized into separate Django applications.
- **Separation of Concerns:** Frontend presentation, backend logic, and data storage remain independent.
- **Reusability:** Shared models and services are reused across application features.
- **Stateless Deployment:** Persistent application data is stored outside individual backend containers.
- **Scalability:** Multiple backend instances can serve requests through a load balancer.

## 4. Frontend Architecture

The frontend is developed using React, Vite, and React Router.

It follows a component-based architecture that separates reusable UI components, application pages, feature-specific functionality, and API communication.

The frontend provides:

- Recipe browsing, searching, and filtering.
- Ingredient-based recipe discovery.
- Personal ingredient inventory management.
- User dashboard and profile settings.
- Dietary preference and allergy management.
- Saved recipes and recipe submission.
- Authentication through Amazon Cognito.

The frontend communicates with Django through REST APIs using a shared API client.

Business logic such as recipe matching, permission enforcement, and persistent data management remains in the backend.

## 5. Authentication and Authorization

Authentication is provided by **Amazon Cognito User Pools**, with Google federation supported through Cognito's hosted authentication interface.

The frontend uses the OAuth 2.0 Authorization Code flow with PKCE.

### Authentication Flow

```text
User
 │
 ▼
React Frontend
 │
 ▼
Amazon Cognito / Google Sign-In
 │
 ▼
Authorization Code + PKCE
 │
 ▼
Cognito Access Token
 │
 ▼
React API Client
 │
 ▼
Django REST Framework
 │
 ├── Validate Cognito JWT
 ├── Map Cognito identity to Django User
 └── Enforce application permissions
```

The frontend sends the Cognito access token in authenticated API requests.

```http
Authorization: Bearer <access_token>
```

Django validates the token's signature, issuer, expiration, token type, and application client ID.

Authenticated identities are mapped to local application users using the Cognito issuer and subject (`sub`).

### User Access

| User Type | Supported Functionality |
|---|---|
| Guest | Browse, search, filter, and discover recipes |
| Registered User | Guest features plus personal inventory, preferences, allergies, saved recipes, and recipe submission |
| Administrator | Application-level administrative permissions where implemented |

The dedicated administrative management interface remains future development.

Django enforces authorization and resource ownership. The frontend may hide protected actions but is not responsible for authoritative permission decisions.

## 6. Recipe and Ingredient Management

Recipes are stored in PostgreSQL and associated with canonical Ingredient records through RecipeIngredient relationships.

Recipe information includes ingredients, cooking instructions, classifications, and associated images.

The application supports recipe browsing, searching, filtering, and authenticated recipe submission.

Submitted recipes are associated with the authenticated user, and duplicate recipe names are checked during submission.

### Initial Recipe Data

The production database was populated using [TheMealDB API](https://www.themealdb.com/api.php) to provide an initial dataset for application functionality and testing.

The imported dataset contains **100 recipes with associated images**.

Recipe images are stored in Amazon S3, while PostgreSQL stores the corresponding application data and media references.

## 7. Recipe Recommendation System

The recommendation system matches recipes against ingredients selected by users or stored in their personal inventories.

The backend supports two matching modes:

| Mode | Behavior |
|---|---|
| `AVAILABLE_ONLY` | Returns recipes whose required ingredients are all available |
| `PARTIAL_MATCH` | Returns recipes with at least one matching required ingredient |

Recommendation results can include matching and missing ingredient information.

The recommendation system also supports filtering based on recipe classifications and allergens.

Authenticated users can save their dietary preferences and allergies, which are automatically considered during applicable recipe browsing and filtering.

Recommendation calculations are performed in Django rather than React.

## 8. Database and Media Storage

### PostgreSQL

Amazon RDS PostgreSQL stores persistent application data, including:

- User accounts and profiles.
- Ingredients and recipe information.
- RecipeIngredient relationships.
- Personal inventories.
- Dietary preferences and allergies.
- Saved recipes and recipe ownership.

Database relationships and models are described in [Database Design](database-design.md).

### Amazon S3

A private Amazon S3 bucket stores recipe images.

The backend accesses media storage using AWS permissions and stores media references in the database rather than storing image binaries directly.

This separates persistent storage from individual backend instances.

## 9. Production Deployment and Scalability

The application is deployed on AWS using CloudFormation-managed infrastructure.

### Frontend

The React application is built into static files and stored in a private Amazon S3 bucket. Amazon CloudFront serves the application using Origin Access Control (OAC).

### Backend

The Django backend runs inside Docker containers on Amazon EC2 instances.

An EC2 Auto Scaling Group maintains two backend instances across two Availability Zones, with a maximum capacity of three instances.

An internal Application Load Balancer distributes incoming API requests across healthy backend instances.

### Networking and Security

The production infrastructure includes:

- Private application subnets for backend instances.
- An internal Application Load Balancer.
- Amazon RDS in private networking.
- VPC endpoints for supported AWS service communication.
- A NAT Gateway for required outbound internet access.
- AWS Systems Manager for private instance management.
- IAM roles and security groups for controlled access.

Docker images are stored in Amazon ECR and pulled by backend instances through VPC endpoints.

Additional infrastructure details are documented in [AWS Architecture](aws-architecture.md).

## 10. Testing and Validation

The application was validated through automated backend tests, functional verification, and API load testing.

The final backend test run completed with **359 successful tests and one skipped test**.

ApacheBench was used to evaluate API behavior under different concurrency levels, including 10, 50, and 100 concurrent requests.

AWS resource utilization and backend health were also monitored to verify that the deployed application remained operational.

## 11. Future Improvements

Potential future development includes:

- Administrative management interface.
- Recipe reviews and ratings.
- Shopping list functionality.
- AI-powered recipe recommendations and assistant.
- Enhanced allergen information and filtering.
- Additional monitoring and security controls.
- Multi-AZ RDS deployment.
- Improved infrastructure redundancy and CI/CD automation.

## 12. Related Documentation

- [Requirements](requirements.md) — Original project requirements.
- [Database Design](database-design.md) — Persistent models and relationships.
- [API Design](api-design.md) — REST API contracts and endpoints.
- [AWS Architecture](aws-architecture.md) — Infrastructure, networking, and deployment.
- [Main README](../README.md) — Project overview.
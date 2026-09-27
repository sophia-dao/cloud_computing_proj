# System Design

## 1. Purpose

This document describes the software architecture and design principles of the Recipe Suggestion App.

The system is designed as a modular cloud-based web application consisting of:

- A React frontend.
- A Django REST Framework backend.
- A relational PostgreSQL database.
- Cloud-based media storage.
- AWS-based deployment infrastructure.

The frontend and backend are independent application components that communicate through a REST API.

---

# 2. Design Goals

The architecture prioritizes:

- Modularity.
- Separation of concerns.
- Reusability.
- Maintainability.
- Scalability.
- Testability.
- Clear ownership of responsibilities.
- Object-oriented and component-based design.

The system should remain simple enough for the project team to understand and maintain while allowing individual components to grow as application requirements increase.

---

# 3. Design Philosophy

## 3.1 Domain-Oriented Modular Design

The application will be organized around major application domains where practical.

Current domains include:

```text
Users / Authentication
Recipes
Ingredients / Inventory
Recommendations
Reviews
Shopping Lists
```

Frontend and backend modules should conceptually correspond to these domains:

```text
Frontend                    Backend

auth/             <---->    users/
recipes/          <---->    recipes/
inventory/        <---->    inventory/
recommendations/  <---->    recommendations/
reviews/          <---->    reviews/
shopping/         <---->    shopping/
```

The frontend and backend remain independent implementations and communicate through defined API interfaces.

---

## 3.2 Object-Oriented Design

Object-oriented principles shall be used where they provide meaningful organization and abstraction.

Important principles include:

- Encapsulation.
- Abstraction.
- Clear responsibilities.
- High cohesion.
- Low coupling.
- Reusability.
- Defined interfaces between modules.

Object-oriented design does not mean that every piece of application code must be implemented as a class.

Classes should represent meaningful domain concepts or responsibilities rather than being created solely to satisfy an object-oriented programming style.

---

## 3.3 Frontend Design Philosophy

The React frontend will use a component-based, modular architecture.

Modern React functional components and hooks should be preferred where appropriate.

Object-oriented principles on the frontend will primarily be achieved through:

- Component encapsulation.
- Reusable components.
- Feature modules.
- Clear interfaces.
- Service abstractions.
- Separation between presentation and application logic.

For example:

```text
Recipe Feature
│
├── RecipeList
│   └── RecipeCard
│
├── RecipeDetails
│   ├── IngredientList
│   ├── RecipeInstructions
│   └── ReviewSection
│
├── RecipeFilter
└── RecipeForm
```

Large components responsible for unrelated functionality should be avoided.

---

## 3.4 Backend Design Philosophy

The Django backend will use domain-focused Django applications.

Django models will represent persistent domain entities and relationships.

Business operations involving multiple models or significant application logic should be separated into appropriate services or modules where doing so improves maintainability.

For example:

```text
UserInventory
      │
      │
      ├─────────────┐
      ▼             ▼
Ingredient       Recipe
      │             │
      └──────┬──────┘
             ▼
   RecommendationService
```

Recommendation logic should not be placed entirely inside the `Recipe` or `User` model because the operation involves multiple application domains.

---

## 3.5 Avoid Overengineering

Abstractions should be introduced when they solve a real design problem.

The project should avoid:

- Classes with no meaningful responsibility.
- Services that simply wrap one trivial model operation.
- Excessive inheritance.
- Duplicate abstraction layers.
- Unnecessary design patterns.
- Premature microservice separation.

The initial application will use a modular monolithic backend rather than separate backend microservices.

This provides clear module boundaries while keeping deployment and development manageable.

---

# 4. High-Level Application Architecture

```text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │ React Frontend  │
                  └────────┬────────┘
                           │
                           │ HTTPS / REST
                           ▼
                  ┌─────────────────┐
                  │ Django REST API │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Business Logic  │
                  │    / Services   │
                  └────────┬────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          ┌────────────┐       ┌────────────┐
          │ PostgreSQL │       │   Media    │
          │    Data    │       │   Storage  │
          └────────────┘       └────────────┘
```

The application will be deployed using AWS infrastructure.

Detailed AWS deployment architecture is documented separately in `aws-architecture.md`.

---

# 5. Frontend Architecture

## 5.1 Proposed Structure

```text
frontend/
├── public/
│
├── src/
│   ├── app/
│   │   ├── App.jsx
│   │   └── routes.jsx
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── profile/
│   │   ├── recipes/
│   │   ├── inventory/
│   │   ├── recommendations/
│   │   ├── reviews/
│   │   └── shopping/
│   │
│   ├── components/
│   │   └── shared/
│   │
│   ├── services/
│   │   └── api/
│   │
│   ├── hooks/
│   ├── utils/
│   └── main.jsx
│
└── package.json
```

The structure may evolve as implementation requirements become clearer.

---

## 5.2 Feature Modules

Each major application domain should primarily own its feature-specific frontend functionality.

For example:

```text
features/
└── recipes/
    ├── components/
    │   ├── RecipeCard.jsx
    │   ├── RecipeList.jsx
    │   ├── RecipeDetails.jsx
    │   └── RecipeFilter.jsx
    │
    ├── hooks/
    │
    ├── services/
    │   └── recipeService.js
    │
    └── utils/
```

Not every feature requires every subdirectory.

Directories should only be created when they serve a meaningful organizational purpose.

---

## 5.3 Shared Components

Components that are genuinely reusable across multiple application domains should be stored separately.

Examples may include:

```text
components/shared/
├── Button.jsx
├── Input.jsx
├── Modal.jsx
├── LoadingIndicator.jsx
└── ErrorMessage.jsx
```

Feature-specific components should remain within their feature module rather than automatically being placed into the shared component directory.

---

# 6. Backend Architecture

## 6.1 Proposed Structure

```text
backend/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── apps/
│   ├── users/
│   ├── recipes/
│   ├── inventory/
│   ├── recommendations/
│   ├── reviews/
│   └── shopping/
│
├── manage.py
└── requirements/
```

The backend will initially operate as a **modular monolith**.

All Django applications are deployed together as one backend application while maintaining clear logical boundaries between domains.

---

## 6.2 Django Application Structure

A Django domain application may contain:

```text
recipes/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── permissions.py
├── services.py
└── tests/
```

Not every application is required to contain every file.

For example, a `services.py` file should only exist when meaningful business logic needs to be separated from models or API views.

---

# 7. Application Layers

Backend responsibilities should generally follow:

```text
HTTP Request
     │
     ▼
┌──────────────────┐
│ API / View Layer │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Business Logic   │
│ / Service Layer  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Domain / Models  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Persistence      │
└──────────────────┘
```

### API Layer

Responsible for:

- Receiving HTTP requests.
- Request validation.
- Authentication/authorization checks.
- Calling appropriate application functionality.
- Returning HTTP responses.

### Business / Service Layer

Responsible for complex business operations such as:

- Recipe recommendation.
- Shopping list generation.
- Operations involving multiple domain models.

Not every operation requires a service.

### Domain / Model Layer

Responsible for:

- Application entities.
- Entity relationships.
- Model-level constraints.
- Appropriate domain behavior.

### Persistence Layer

Primarily implemented through Django's ORM and external storage integrations.

---

# 8. Frontend–Backend Communication

React shall communicate with Django through REST APIs.

Normal application communication follows:

```text
React Component
      │
      ▼
Feature Service / API Client
      │
      │ HTTP
      ▼
Django REST Endpoint
      │
      ▼
Application Logic
      │
      ▼
Database / Storage
```

For example:

```text
InventoryPage
      │
      ▼
inventoryService
      │
      │ GET /api/inventory/
      ▼
Inventory API
      │
      ▼
Inventory Logic
      │
      ▼
PostgreSQL
```

React components should not contain knowledge of database implementation details.

---

# 9. Guest and Authenticated State

The core recipe discovery functionality shall support both guests and authenticated users.

Guest state may exist temporarily within the frontend or other appropriate temporary storage.

For example:

```text
Guest

Temporary Ingredients
        │
        ▼
Recommendation Request
        │
        ▼
Recipe Results
        │
        ▼
Temporary Shopping List
```

Authenticated users gain persistence:

```text
Registered User

Persistent Inventory
        │
        ▼
Recommendation Request
        │
        ▼
Recipe Results
        │
        ├── Save Recipe
        │
        └── Save Shopping List
```

The recommendation system should not require separate recommendation implementations for guests and authenticated users.

Instead, both should ultimately provide a compatible ingredient/filter input to the same recommendation logic.

---

# Core Business Logic Independence

Core business logic should operate independently of whether the request originates from a Guest or an authenticated Registered User whenever possible.

Authentication determines the availability and persistence of user-specific data, but should not require separate implementations of the same core application functionality.

For example, the recommendation system accepts ingredient and preference information regardless of its source:

```text
Guest Ingredients ──────────┐
                            │
                            ▼
                   RecommendationService
                            │
                            ▼
                   Recipe Recommendations
                            ▲
                            │
Saved User Inventory ───────┘
```

The recommendation service should receive a consistent input structure such as:

```text
RecommendationInput
├── ingredients
├── allergies
├── dietary_preferences
├── cuisine_filters
└── other_filters
```

For a Guest, this information may originate from temporary frontend or session state.

For an authenticated user, the same information may originate from persistent account data.

The `RecommendationService` should not require separate recommendation algorithms for Guests and Registered Users.

The same principle should be applied to other shared business operations where appropriate.

For example:

```text
Guest Ingredients ──────────┐
                            │
                            ▼
                    ShoppingListService
                            │
                            ▼
                  Generated Shopping List
                            ▲
                            │
Saved User Inventory ───────┘
```

The resulting shopping list may remain temporary for a Guest, while an authenticated user may persist the result to their account.

### Design Rule

> Authentication should determine identity, authorization, personalization, and persistence—not unnecessarily duplicate core business logic.

This approach reduces duplicated code, keeps business rules consistent between Guests and Registered Users, and allows core application services to evolve independently from authentication and persistence mechanisms.

---

# 10. Authorization Model

The application uses hierarchical access:

```text
Guest
  │
  ▼
Registered User
  │
  ▼
Administrator
```

A Registered User has all Guest functionality plus authenticated account functionality.

An Administrator has all Registered User functionality plus administrative permissions.

Administrators shall continue to have access to the normal user-facing application.

Authorization should be enforced by the backend.

Frontend interface restrictions may improve usability but shall not be considered sufficient authorization.

For example, hiding an Admin button in React does not replace backend permission checking.

---

# 11. Recommendation Architecture

The initial recommendation system shall not depend on artificial intelligence.

Conceptually:

```text
Available Ingredients
        +
Selected Filters
        +
Allergies / Preferences
        │
        ▼
Recommendation Service
        │
        ├── Filter incompatible recipes
        ├── Compare recipe ingredients
        ├── Determine missing ingredients
        └── Calculate recommendation score
        │
        ▼
Ranked Recipe Results
```

The recommendation logic should remain sufficiently separated from presentation and infrastructure code so that the algorithm can be modified later.

Future AI functionality may supplement this system but should not be required for core recipe recommendations.

---

# 12. Media Architecture

Application media shall not be stored inside backend containers.

Django will maintain references to media associated with application entities.

Conceptually:

```text
Recipe
  │
  ├── Recipe Data ──────── PostgreSQL
  │
  └── Recipe Image ─────── Cloud Object Storage
```

This ensures media remains persistent independently of backend container deployment and scaling.

Detailed AWS media architecture is documented in `aws-architecture.md`.

---

# 13. Deployment Boundary

The system contains two independently deployable application components:

```text
┌────────────────────────────┐
│      React Frontend        │
└────────────────────────────┘

              REST

┌────────────────────────────┐
│ Django REST API Backend    │
│     Docker Container       │
└────────────────────────────┘
```

The backend is packaged as a Docker container.

Persistent database data and media shall remain external to the backend container.

This allows backend containers to be replaced, restarted, or scaled without losing persistent application information.

---

# 14. Design Rules

Team members should follow these general rules when implementing application functionality:

1. Give components, classes, and modules clear responsibilities.
2. Keep related functionality together.
3. Minimize unnecessary dependencies between unrelated domains.
4. Avoid large components or classes responsible for unrelated functionality.
5. Avoid duplicated business logic.
6. Use reusable components and services where reuse is meaningful.
7. Keep frontend presentation separate from backend business logic.
8. Keep cloud infrastructure concerns separate from application business logic.
9. Communicate between frontend and backend through defined API contracts.
10. Enforce authorization on the backend.
11. Do not rely on frontend visibility to enforce permissions.
12. Do not store persistent data inside application containers.
13. Avoid introducing abstractions without a clear benefit.
14. Prefer composition over unnecessary inheritance.
15. Keep the initial system simple enough for the team to understand and maintain.
16. Document significant architectural changes.

---

# 15. Related Documentation

```text
README.md
    High-level project overview

docs/
├── requirements.md
│   Functional and non-functional requirements
│
├── system-design.md
│   Software architecture and design philosophy
│
├── database-design.md
│   Database entities and relationships
│
├── api-design.md
│   REST API contracts
│
└── aws-architecture.md
    AWS infrastructure and deployment
```

The architecture described in this document may evolve as project requirements and implementation constraints become clearer. Significant changes should be documented so that the team maintains a consistent understanding of the system.
# System Design

## 1. Purpose

This document describes the software architecture and design principles of the Recipe Suggestion App.

The system is designed as a modular, cloud-based web application with a React frontend and a Django REST Framework backend. The frontend and backend communicate through a REST API and are designed as separate application layers.

The architecture prioritizes:

- Modularity.
- Separation of concerns.
- Reusability.
- Maintainability.
- Scalability.
- Clear ownership of responsibilities.
- Object-oriented and component-based design.

---

# 2. Design Philosophy

## 2.1 Full-Stack Modular Design

The application will follow a modular, domain-oriented architecture across both the frontend and backend.

Instead of organizing the entire application around technical file types, functionality should be grouped around application domains where practical.

Major domains currently include:

- Authentication and users.
- Recipes.
- Ingredient inventory.
- Recommendations.
- Reviews.
- Shopping lists.

This creates a conceptual relationship between frontend and backend functionality:

```text
Frontend                    Backend

auth/             <---->    users/
recipes/          <---->    recipes/
inventory/        <---->    inventory/
recommendations/  <---->    recommendations/
reviews/          <---->    reviews/
shopping/         <---->    shopping/
```

The frontend and backend remain independent applications and communicate through defined REST API interfaces.

---

## 2.2 Object-Oriented Design

Object-oriented design principles will be applied where appropriate throughout the application.

The goal is not to require every piece of code to be implemented as a class. Instead, the project will apply principles commonly associated with good object-oriented software design, including:

- Encapsulation.
- Abstraction.
- Separation of responsibilities.
- Reusability.
- Clear interfaces between components.
- Low coupling between unrelated modules.
- High cohesion within related modules.

Classes and objects should represent meaningful concepts or responsibilities rather than being introduced only for the purpose of using object-oriented syntax.

---

## 2.3 Backend Design Philosophy

The Django backend will use object-oriented design through Django models, domain objects, services, and other appropriate abstractions.

Business responsibilities should be separated where doing so improves maintainability.

For example:

```text
Recipe
    │
    ├── represents recipe data and relationships
    │
    ▼
RecipeService
    │
    ├── performs recipe-related business operations
    │
    ▼
RecommendationService
    │
    └── performs recommendation-specific logic
```

A Django model should not become responsible for every operation related to its domain.

For example, recommendation logic involving users, inventories, preferences, and multiple recipes should not be placed entirely inside the `Recipe` model.

Instead, functionality involving multiple domain objects should be placed in an appropriate service or module.

---

## 2.4 Frontend Design Philosophy

The React frontend will follow component-based and modular design principles.

Modern React functional components and hooks will be preferred where appropriate.

Object-oriented design on the frontend does **not** mean that all React components must be implemented using JavaScript class components.

Instead, frontend code should apply the same underlying software engineering principles:

- Encapsulation of component behavior.
- Reusable components.
- Clear responsibilities.
- Abstraction of external communication.
- Separation of presentation and application logic.
- Modular organization.

For example, recipe functionality should be divided into reusable components rather than implemented as one large page:

```text
Recipe Feature

RecipeList
    │
    └── RecipeCard

RecipeDetails
    │
    ├── IngredientList
    ├── RecipeInstructions
    └── ReviewSection

RecipeFilter

RecipeForm
```

Each component should have a clear responsibility.

---

## 2.5 Separation of Concerns

The system should separate responsibilities between application layers.

At a high level:

```text
┌─────────────────────────────┐
│       Presentation          │
│          React              │
└──────────────┬──────────────┘
               │
               │ REST / HTTPS
               ▼
┌─────────────────────────────┐
│          API Layer          │
│   Django REST Framework     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Business Logic         │
│     Services / Domain       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Data / Storage        │
│   PostgreSQL / S3 / etc.    │
└─────────────────────────────┘
```

Responsibilities should not unnecessarily cross these boundaries.

For example:

- React should not directly communicate with PostgreSQL.
- React should communicate with the backend through the REST API.
- API endpoints should not contain large amounts of unrelated business logic.
- Database models should primarily represent application data and domain relationships.
- Complex operations involving multiple models should be handled by appropriate services.
- Infrastructure-specific concerns should remain separate from application business logic.

---

## 2.6 Reusability

Common functionality should be reusable rather than duplicated.

For example, the frontend should provide reusable interface components where appropriate:

```text
Button
Input
Modal
LoadingIndicator
RecipeCard
IngredientTag
RatingDisplay
```

Similarly, backend functionality that is shared across multiple endpoints should be implemented in reusable services, utilities, serializers, permissions, or other appropriate abstractions.

Reusability should not be forced when two pieces of functionality only appear superficially similar.

---

## 2.7 High Cohesion and Low Coupling

Modules should have **high cohesion**, meaning that related functionality is kept together.

Modules should also have **low coupling**, meaning that unrelated modules should depend on each other as little as practical.

For example:

```text
inventory/
├── IngredientList
├── IngredientItem
├── AddIngredientForm
└── inventoryService
```

These components belong together because they are responsible for the same application domain.

Recipe functionality should not need to know how inventory interface components are internally implemented.

Communication between domains should occur through clearly defined interfaces.

---

## 2.8 Dependency Direction

Higher-level application functionality should avoid unnecessary dependency on infrastructure-specific implementation details.

For example, recommendation logic should conceptually operate on recipes and ingredients rather than being tightly coupled to AWS infrastructure.

```text
Recommendation Logic
        │
        ▼
Recipe / Ingredient Data

NOT

Recommendation Logic
        │
        ▼
AWS-specific implementation
```

This makes application logic easier to test and allows infrastructure implementations to change with less impact on business logic.

---

# 3. High-Level Application Architecture

The application consists of two primary application components:

1. React web frontend.
2. Django REST Framework backend.

The frontend communicates with the backend through REST APIs.

```text
                         User
                           │
                           ▼
                    React Frontend
                           │
                           │ HTTPS / REST
                           ▼
                 Django REST Framework
                           │
                    Business Logic
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
             PostgreSQL             Media
               Data                Storage
```

The application components will be deployed using AWS infrastructure.

Detailed AWS infrastructure is documented separately in `aws-architecture.md`.

---

# 4. Frontend Architecture

The frontend will be implemented using React.

The frontend should be organized primarily around application features.

A proposed structure is:

```text
frontend/
└── src/
    ├── app/
    │   ├── App.jsx
    │   └── routes.jsx
    │
    ├── features/
    │   ├── auth/
    │   ├── profile/
    │   ├── recipes/
    │   ├── inventory/
    │   ├── recommendations/
    │   ├── reviews/
    │   └── shopping/
    │
    ├── components/
    │   └── shared/
    │
    ├── services/
    │   └── api/
    │
    └── utils/
```

Individual feature directories may contain their own:

```text
components/
hooks/
services/
utils/
```

when required.

Not every feature must contain every directory. Directories should only be introduced when they serve a clear purpose.

---

# 5. Backend Architecture

The backend will be implemented using Django and Django REST Framework.

Backend functionality will be separated into domain-focused Django applications.

A proposed structure is:

```text
backend/
├── config/
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

Each Django application owns functionality related to its domain.

For example:

```text
recipes/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── services.py
└── tests/
```

The exact internal structure may evolve as implementation requirements become clearer.

Files such as `services.py` should only be introduced where a service layer provides meaningful separation of business logic.

---

# 6. Frontend–Backend Communication

The frontend shall not access application databases or cloud storage directly unless explicitly required by the system design.

Normal application operations will follow:

```text
React Component
      │
      ▼
Frontend Service / API Client
      │
      │ HTTP Request
      ▼
Django REST API
      │
      ▼
Business Logic
      │
      ▼
Data Layer
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
Django Inventory API
      │
      ▼
Inventory Domain Logic
      │
      ▼
PostgreSQL
```

This prevents UI components from becoming tightly coupled to backend implementation details.

---

# 7. Design Rules

The following rules should guide implementation decisions:

1. Components and classes should have a clear responsibility.
2. Avoid large components or classes responsible for unrelated functionality.
3. Avoid duplicated business logic.
4. Prefer reusable components and services where reuse is meaningful.
5. Keep frontend presentation separate from backend business logic.
6. Keep infrastructure concerns separate from application business logic.
7. Communicate between frontend and backend through defined API interfaces.
8. Keep domain-related functionality together.
9. Avoid unnecessary dependencies between unrelated features.
10. Do not introduce abstractions solely for the sake of abstraction.
11. Prefer simple implementations when additional complexity provides no clear architectural benefit.
12. Design modules so they can be tested independently where practical.

The architecture may evolve as project requirements become clearer. Significant architectural changes should be documented so that all team members follow the same design conventions.
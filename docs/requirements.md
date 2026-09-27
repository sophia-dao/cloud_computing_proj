# System Requirements

## 1. Purpose

This document defines the functional and non-functional requirements for the Recipe Suggestion App.

The application is intended to help users discover recipes based on ingredients they already have while considering personal preferences, dietary restrictions, allergies, and other supported filters.

This document defines **what the system is expected to do**. Implementation and architectural details are documented separately in the system design and AWS architecture documentation.

---

# 2. User Roles

The system will initially support the following user roles.

## 2.1 Guest

A guest is a user who has not authenticated with an account.

Guests may access supported public functionality such as:

- Viewing recipes.
- Searching recipes.
- Viewing recipe ratings and reviews.

Features requiring personal user data shall require authentication.

## 2.2 Registered User

A registered user has an authenticated account and access to personalized functionality including:

- Personal dashboard.
- Ingredient inventory.
- User preferences and allergies.
- Personalized recipe recommendations.
- Shopping lists.
- Recipe creation.
- Recipe reviews and ratings.
- Account settings.

## 2.3 Administrator

An administrator has additional permissions for managing application content and users.

---

# 3. Functional Requirements

## FR-01 — User Registration

The system shall allow users to create an account.

Account information shall be stored persistently and associated with the user's application data.

---

## FR-02 — User Authentication

The system shall allow registered users to:

- Log in.
- Log out.
- Access protected functionality while authenticated.

The system shall identify the currently authenticated user when accessing user-specific resources.

Users shall not be able to access another user's private data through modification of client requests.

---

## FR-03 — User Profile

The system shall allow registered users to maintain a user profile.

The profile may contain:

- Display name.
- Profile image/avatar.
- Dietary preferences.
- Allergies.
- Cuisine preferences.
- Other supported application preferences.

The exact visual representation of the logged-in user will be determined during UI/UX design.

---

## FR-04 — Personalized User Interface

The system shall provide an authenticated user interface for registered users.

When authenticated, the application shall recognize the current user and display appropriate account information within the interface.

This may include:

- Display name.
- Username.
- Profile image/avatar.
- Other supported account identifiers.

The interface shall provide access to user-specific functionality and provide a method for the user to access account settings and log out.

---

## FR-05 — User Dashboard

The system shall provide authenticated users with a personalized dashboard.

The dashboard shall provide access to major user-specific functionality including:

- Recipe recommendations.
- Ingredient inventory.
- Recipe search.
- Shopping list.
- User preferences.
- Account settings.

The dashboard may additionally display information such as:

- Recently viewed recipes.
- Inventory summaries.
- Suggested recipes.
- Other relevant personalized information.

The exact dashboard layout will be determined during UI/UX design.

---

## FR-06 — Ingredient Inventory

The system shall allow authenticated users to maintain a personal inventory of available ingredients.

Users shall be able to:

- Add ingredients.
- View ingredients.
- Update ingredients.
- Remove ingredients.

Ingredient inventory information shall be associated with the authenticated user's account and stored persistently.

---

## FR-07 — Recipe Management

The system shall maintain recipe information.

A recipe shall be capable of containing:

- Name.
- Description.
- Required ingredients.
- Ingredient quantities.
- Cooking instructions.
- Preparation time.
- Cooking time.
- Cuisine.
- Dietary information.
- Allergen information.
- Cost information or cost category.
- Recipe image where applicable.

---

## FR-08 — Recipe Creation

Authorized users shall be able to manually create recipes.

Recipe creation shall support information including:

- Recipe name.
- Description.
- Ingredients.
- Ingredient quantities.
- Cooking instructions.
- Preparation time.
- Cooking time.
- Cuisine.
- Dietary information.
- Recipe image where applicable.

The system shall validate required recipe information before accepting a new recipe.

---

## FR-09 — Recipe Display

The system shall provide an interface for viewing recipe information.

Recipe pages should display relevant information such as:

- Recipe name.
- Image.
- Description.
- Ingredients.
- Ingredient quantities.
- Cooking instructions.
- Preparation and cooking time.
- Cuisine.
- Dietary information.
- Allergen information.
- Cost information where available.
- Ratings and reviews.

---

## FR-10 — Recipe Search

The system shall allow users to search available recipes.

Search functionality should support relevant information such as:

- Recipe name.
- Ingredients.
- Cuisine.

Search functionality may be expanded as additional recipe metadata becomes available.

---

## FR-11 — Recipe Filtering

The system shall allow recipes to be filtered using supported criteria.

Filters may include:

- Ingredients.
- Dietary preferences.
- Allergies.
- Cuisine.
- Vegan or vegetarian status.
- Halal status.
- Preparation or cooking time.
- Ingredient cost.

Saved user preferences should automatically be applied where appropriate.

---

## FR-12 — Recipe Recommendation

The system shall recommend recipes based primarily on ingredients available in the user's ingredient inventory.

The recommendation process should consider:

- Ingredients the user currently has.
- Ingredients required by recipes.
- Missing ingredients.
- User allergies.
- Dietary preferences.
- Cuisine preferences.
- User-selected filters.

The system should prioritize recipes that make greater use of ingredients already available to the user.

The initial recommendation system does not require artificial intelligence.

---

## FR-13 — Allergy Management

The system shall allow registered users to record supported food allergies.

Saved allergy information shall automatically be considered when providing personalized recipe recommendations and filtering.

Recipes containing ingredients known by the system to conflict with a user's recorded allergies shall be excluded from normal personalized recommendations or clearly identified according to the application's filtering rules.

The application shall not represent its allergy filtering as a substitute for professional medical or food-safety guidance.

---

## FR-14 — Dietary Preferences

The system shall allow registered users to maintain supported dietary preferences.

Examples may include:

- Vegan.
- Vegetarian.
- Halal.
- Other supported dietary classifications.

Saved dietary preferences should automatically affect personalized recipe filtering and recommendations where applicable.

---

## FR-15 — Recipe Reviews and Ratings

Authenticated users shall be able to submit reviews for recipes.

A review shall contain or reference:

- The associated user.
- The associated recipe.
- A rating.
- An optional written comment.
- A creation date.

The system shall be capable of displaying rating information derived from submitted reviews.

---

## FR-16 — Shopping List

The system shall allow authenticated users to maintain a personal shopping list.

When viewing a recipe, the system should be capable of comparing the recipe's required ingredients against the user's ingredient inventory.

The system should identify ingredients required by the recipe that are not currently recorded in the user's inventory.

Users shall be able to add missing ingredients to their shopping list.

Users shall be able to:

- View shopping list items.
- Add shopping list items.
- Update supported shopping list information.
- Remove shopping list items.

---

## FR-17 — Account Settings

Authenticated users shall be able to manage supported account settings and preferences.

Changes shall persist across authenticated sessions.

---

## FR-18 — Media Management

The system shall support media associated with application resources.

Supported media may include:

- Recipe images.
- User profile images or avatars.
- Other supported user-uploaded content.

Media files shall be stored separately from the application's relational database.

The database shall maintain the information necessary to associate stored media with application resources.

The system shall validate supported file types and enforce appropriate upload restrictions.

Media access shall respect applicable authorization and privacy requirements.

---

## FR-19 — Administrative Functionality

Administrators shall have access to protected administrative functionality.

Administrative functionality may include:

- User management.
- Recipe management.
- Review management.
- Application content management.

Administrative functionality shall not be accessible to normal registered users.

---

## FR-20 — Contact and Support

The system shall provide users with a method for submitting questions, feedback, or support requests.

Support submissions should contain sufficient information for administrators or project members to review the request.

---

# 4. Potential / Future Requirements

The following functionality is being considered but is **not currently required for the core application**.

Implementation will depend on project progress, available resources, and technical feasibility.

## FUT-01 — AI-Generated Recipes

The system may allow users to generate recipes based on available ingredients and user-provided instructions using an AI service.

## FUT-02 — AI Recipe Assistant

The system may provide a conversational assistant for recipe discovery and cooking-related questions.

## FUT-03 — Recipe Scanning

The system may allow users to upload or scan recipe information and automatically extract recipe and ingredient data.

## FUT-04 — Advanced Ingredient Tracking

The ingredient inventory may eventually support additional information such as:

- Quantity.
- Measurement units.
- Expiration dates.
- Purchase dates.

## FUT-05 — Advanced Interface Customization

Users may eventually be able to customize additional aspects of the application interface.

## FUT-06 — Advanced Recommendation Features

The recommendation system may eventually incorporate additional recommendation techniques or intelligent personalization.

---

# 5. Non-Functional Requirements

## NFR-01 — Modularity

The application shall use a modular design across both the frontend and backend.

Related functionality should be grouped into clearly defined application domains or modules.

Major modules may include:

- Authentication and users.
- Recipes.
- Ingredient inventory.
- Recommendations.
- Reviews.
- Shopping lists.

Changes to one module should minimize unnecessary impact on unrelated modules.

---

## NFR-02 — Object-Oriented and Component-Based Design

The application shall follow object-oriented and component-based software design principles where appropriate.

Backend development should use clearly defined models, services, and responsibilities.

Frontend development should use reusable and encapsulated React components, modules, hooks, and services where appropriate.

The system should emphasize:

- Encapsulation.
- Abstraction.
- Reusability.
- Clear responsibilities.
- Low coupling.
- High cohesion.

The use of object-oriented principles does not require every component or module to be implemented as a class.

---

## NFR-03 — Separation of Concerns

The application shall maintain separation between major responsibilities including:

- User interface and presentation.
- Frontend application logic.
- API communication.
- Backend API handling.
- Business logic.
- Data models.
- Data persistence.
- Media storage.
- Cloud infrastructure.

Frontend components shall communicate with backend functionality through defined application interfaces rather than directly accessing the application database.

---

## NFR-04 — Maintainability

The application should use consistent:

- Project organization.
- Naming conventions.
- Documentation.
- Coding conventions.
- API conventions.

Components and modules should have clearly defined responsibilities.

Large components or classes responsible for unrelated functionality should be avoided.

---

## NFR-05 — Reusability

Common functionality should be implemented as reusable components, services, utilities, or other appropriate abstractions when meaningful.

Duplicated business logic should be avoided where practical.

Abstractions should not be introduced solely for the purpose of increasing architectural complexity.

---

## NFR-06 — Scalability

The application shall be designed so that major functionality can be extended without requiring significant modification to unrelated components.

The cloud architecture should support scaling application resources as usage increases.

Application state and persistent user data should not depend on the lifetime of an individual backend application instance or container.

---

## NFR-07 — Security

The application shall:

- Protect authenticated functionality.
- Enforce authorization rules.
- Protect private user data.
- Validate user input.
- Validate supported file uploads.
- Store credentials and secrets securely.
- Use secure communication in production.
- Prevent unauthorized access to resources belonging to other users.
- Restrict administrative functionality to authorized accounts.

---

## NFR-08 — Reliability

Persistent application data shall remain available independently of individual backend container deployments, restarts, or replacements.

Failure of optional functionality should not prevent users from accessing the application's core recipe, inventory, account, and recommendation functionality.

---

## NFR-09 — Performance

The application should provide responsive interaction under the expected workload of the project.

Recipe search and recommendation operations should avoid unnecessary processing, database queries, and data transfer.

---

## NFR-10 — Usability

The application should provide an interface that allows users to perform common tasks with minimal unnecessary interaction.

Primary workflows such as:

- Adding ingredients.
- Finding recipes.
- Viewing recommendations.
- Managing shopping lists.

should be easy to locate and use.

The interface should provide clear feedback for user actions, loading states, errors, and successful operations where appropriate.

---

## NFR-11 — Media Storage

The application shall use cloud-based object storage for persistent application media.

Media storage shall remain independent from backend application containers so uploaded media persists across deployments, restarts, scaling operations, and container replacement.

---

## NFR-12 — Cloud Deployment

The application shall be deployable using Amazon Web Services (AWS).

The planned cloud environment includes support for:

- Frontend hosting.
- Containerized backend deployment.
- Relational database hosting.
- Persistent media storage.
- Application networking.
- Monitoring and logging.

Specific AWS infrastructure and configuration are documented separately in the AWS architecture documentation.

---

## NFR-13 — Testability

Application modules should be designed so that individual functionality can be tested independently where practical.

Business logic should not be unnecessarily coupled to frontend presentation or cloud infrastructure.

---

# 6. Core Project Scope

The initial implementation will prioritize:

1. User registration and authentication.
2. Logged-in user interface.
3. Personalized user dashboard.
4. User profile and preferences.
5. Allergy and dietary preference management.
6. Ingredient inventory management.
7. Recipe storage and display.
8. Manual recipe creation.
9. Recipe search and filtering.
10. Ingredient-based recipe recommendations.
11. Reviews and ratings.
12. Shopping list management.
13. Recipe and user media support.
14. Basic administrative functionality.

AI functionality, recipe scanning, advanced inventory tracking, advanced interface customization, and other intelligent features are outside the committed initial scope.

---

# 7. Requirement Priority

Requirements may be prioritized during development according to the following categories:

- **Core:** Required for the primary application workflow.
- **Supporting:** Required to support the overall user experience or system operation.
- **Extended:** Valuable functionality that may be implemented after core functionality is operational.
- **Future:** Functionality under consideration but not currently committed.

The project scope may be adjusted based on development progress, course requirements, technical feasibility, and available project resources.
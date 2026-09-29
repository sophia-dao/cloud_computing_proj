# System Requirements

## 1. Purpose

This document defines the functional and non-functional requirements for the Recipe Suggestion App.

The application is intended to help users discover recipes based on ingredients they currently have while considering dietary restrictions, allergies, cuisine preferences, and other supported filters.

The core recipe discovery functionality shall be available without requiring an account. User accounts provide persistent storage and additional personalized functionality.

This document defines **what the system is expected to do**. Implementation and architectural details are documented separately in the system design and AWS architecture documentation.

---
## 1a. System Design Requirements

### Scalability

The system must be designed to support increased application traffic and data volume without requiring major architectural changes.

The system should support:

- Stateless backend API instances where practical.
- Horizontal scaling of the Django backend.
- Independent scaling of frontend, backend, database, and media storage.
- Pagination for APIs that may return large datasets.
- Appropriate database indexing.
- Efficient database access and avoidance of unnecessary queries.
- Cloud-based object storage for uploaded media.
- Load balancing when multiple backend instances are deployed.
- Monitoring of application and infrastructure performance.
- Load and performance testing using measurable statistics.

Scalability claims must be supported by measured results.

Metrics should include, where applicable:

- Concurrent users
- Requests per second
- Average response time
- p95 response time
- Error rate
- CPU utilization
- Memory utilization
- Database/query performance

The final system documentation should include load-testing results and analysis.

### Security

The system must follow secure design principles across authentication, authorization, API communication, data storage, and AWS infrastructure.

The system should include:

- Amazon Cognito for user authentication.
- Backend authorization and ownership validation.
- HTTPS for production communication.
- Backend input validation.
- Secure management of credentials and secrets.
- AWS IAM permissions following the principle of least privilege.
- Restricted database network access.
- Secure media storage and access controls.
- Environment-specific configuration.
- Logging and monitoring of important application and infrastructure events.
- Protection against unauthorized access to user-specific resources.
- No credentials, passwords, tokens, or secrets committed to source control.

Security controls must be enforced by the backend and infrastructure rather than relying only on frontend behavior.

### Security Validation

Security behavior should be tested.

Examples include:

```text
Guest
→ Public Recipe
✓ Allowed

Guest
→ User Inventory
✗ Rejected

User A
→ User A Inventory
✓ Allowed

User A
→ User B Inventory
✗ Rejected

Invalid / Expired Token
→ Protected API
✗ Rejected
```

The final documentation should describe the security architecture and provide evidence that major authorization controls were tested.

---

# 2. User Roles and Access Model

The application will use a hierarchical access model.

Higher-level roles inherit the functionality available to lower-level roles:

```text
Guest
  │
  │ + Persistent account functionality
  ▼
Registered User
  │
  │ + Administrative functionality
  ▼
Administrator
```

Therefore:

- A **Guest** has access to the application's core public functionality.
- A **Registered User** has access to all Guest functionality plus account-specific and persistent functionality.
- An **Administrator** has access to all Registered User functionality plus administrative functionality.

---

## 2.1 Guest

A Guest is a user who accesses the application without authenticating with an account.

Guests shall be able to use the application's core recipe functionality, including:

- Browse recipes.
- Search recipes.
- View recipe details.
- Enter available ingredients.
- Modify their current ingredient selection.
- Receive recipe recommendations.
- Apply supported recipe filters.
- Enter allergy and dietary filters.
- Generate shopping lists based on missing ingredients.
- View recipe ratings and reviews.

Guest-specific information may be stored temporarily for the current session but is not required to persist across sessions.

---

## 2.2 Registered User

A Registered User is an authenticated application user.

Registered Users shall have access to **all functionality available to Guests**.

In addition, Registered Users shall have access to functionality requiring persistent user identity and storage, including:

- Save and manage a persistent ingredient inventory.
- Save recipes.
- Access previously saved recipes.
- Save and manage shopping lists.
- Save dietary preferences.
- Save allergy information.
- Save supported recipe preferences.
- Submit recipe ratings and reviews.
- Access a personalized dashboard.
- Manage account and profile information.
- Access other supported account-specific functionality.

The primary distinction between a Guest and a Registered User is the ability to associate persistent information and user-generated content with an authenticated account.

---

## 2.3 Administrator

An Administrator is an authenticated Registered User with additional administrative permissions.

Administrators shall have access to **all functionality available to Registered Users**, including the normal user-facing application interface.

Administrators shall additionally have access to authorized administrative functionality, which may include:

- User management.
- Recipe management.
- Review management.
- Application content management.
- Moderation functionality.
- Other administrative tools introduced by the system.

Administrative functionality shall only be available to accounts with the required permissions.

Administrators should be able to use the application as normal users without requiring a separate account or separate user-facing application.

---

## 2.4 Access Summary
```
                    Application
                        │
             ┌──────────┴──────────┐
             │                     │
       Public Features       Authenticated Features
             │                     │
       Everyone can use        User required
                                   │
                           ┌───────┴────────┐
                           │                │
                      User Features   Admin Features
                                           │
                                    permission required
```

| Functionality | Guest | Registered User | Administrator |
| --- | :---: | :---: | :---: |
| Browse recipes | ✓ | ✓ | ✓ |
| Search recipes | ✓ | ✓ | ✓ |
| View recipe details | ✓ | ✓ | ✓ |
| Enter ingredients | ✓ | ✓ | ✓ |
| Receive recipe recommendations | ✓ | ✓ | ✓ |
| Apply filters | ✓ | ✓ | ✓ |
| Generate shopping list | ✓ | ✓ | ✓ |
| View ratings/reviews | ✓ | ✓ | ✓ |
| Save ingredient inventory | — | ✓ | ✓ |
| Save recipes | — | ✓ | ✓ |
| Save shopping lists | — | ✓ | ✓ |
| Save preferences/allergies | — | ✓ | ✓ |
| Submit ratings/reviews | — | ✓ | ✓ |
| Personalized dashboard | — | ✓ | ✓ |
| Account/profile management | — | ✓ | ✓ |
| Administrative dashboard | — | — | ✓ |
| User/content management | — | — | ✓ |

---

# 3. Functional Requirements

## FR-01 — User Registration

The system shall allow guests to create an account.

Creating an account shall provide access to functionality requiring persistent user data.

---

## FR-02 — User Authentication

The system shall allow registered users to:

- Log in.
- Log out.
- Access account-specific functionality while authenticated.

The system shall identify the currently authenticated user when accessing account-specific resources.

Users shall not be able to access another user's private data through modification of client requests.

---

## FR-03 — User Profile

The system shall allow registered users to maintain a profile.

The profile may contain:

- Display name.
- Profile image/avatar.
- Dietary preferences.
- Allergies.
- Cuisine preferences.
- Other supported application preferences.

The exact visual representation of the logged-in user will be determined during UI/UX design.

---

## FR-04 — Authenticated User Interface

The system shall provide additional account-related interface functionality when a registered user is authenticated.

The application shall indicate that the user is currently authenticated using appropriate account information such as:

- Display name.
- Username.
- Profile image/avatar.
- Other supported account identifiers.

The exact presentation will be determined during UI/UX design.

The authenticated interface shall provide access to account-specific functionality and a method for the user to log out.

---

## FR-05 — User Dashboard

The system shall provide authenticated users with a personalized dashboard.

The dashboard shall provide access to persistent user information and functionality including:

- Saved recipes.
- Saved ingredient inventory.
- Saved shopping lists.
- Recipe recommendations.
- User preferences.
- Allergy settings.
- Account settings.

The dashboard may additionally display:

- Recently viewed recipes.
- Inventory summaries.
- Suggested recipes.
- Other relevant personalized information.

---

## FR-06 — Ingredient Input and Inventory

The system shall allow both guests and registered users to provide ingredients they currently have available.

Users shall be able to:

- Add ingredients.
- View selected ingredients.
- Update supported ingredient information.
- Remove ingredients.

For guests, ingredient information may exist only for the current session and is not required to persist after the session ends.

For authenticated users, the system shall allow the ingredient information to be stored as a persistent personal inventory associated with their account.

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

Authorized authenticated users shall be able to manually create recipes.

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

Guests and registered users shall be able to view recipe information.

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

Guests and registered users shall be able to search available recipes.

Search functionality should support relevant information such as:

- Recipe name.
- Ingredients.
- Cuisine.

Search functionality may be expanded as additional recipe metadata becomes available.

---

## FR-11 — Recipe Filtering

Guests and registered users shall be able to filter recipes using supported criteria.

Filters may include:

- Ingredients.
- Dietary preferences.
- Allergies.
- Cuisine.
- Vegan or vegetarian status.
- Halal status.
- Preparation or cooking time.
- Ingredient cost.

Guests may manually select filters for their current session.

Saved preferences belonging to authenticated users should automatically populate or apply supported filters where appropriate.

---

## FR-12 — Recipe Recommendation

Guests and registered users shall be able to receive recipe recommendations based on the ingredients they provide.

The recommendation system shall support at least two ingredient matching modes.

### Mode 1 — Available Ingredients Only

The system shall provide a mode that returns recipes whose required ingredients are entirely contained within the ingredients currently available to the user.

A recipe is eligible when all required ingredients for the recipe are available to the user.

The recipe is not required to use every ingredient available to the user.

Conceptually:

```text id="xrbjke"
Recipe Ingredients ⊆ User Ingredients
```

Example:

```text id="9k5s21"
User Ingredients:

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
Cabbage
Kimchi
→ Eligible


Recipe C:
Egg
Rice
→ Not Eligible
```

This mode allows users to find recipes they can prepare without requiring additional ingredients.

### Mode 2 — Partial Ingredient Match

The system shall provide a mode that returns recipes using one or more ingredients currently available to the user, even when the recipe requires additional ingredients.

Conceptually:

```text id="v3q1nd"
Recipe Ingredients ∩ User Ingredients ≠ ∅
```

Recipes should be ranked according to how well they match the user's available ingredients.

The system should provide information indicating:

- Ingredients the user already has.
- Ingredients the user is missing.
- Ingredient match information or score.

For example:

```text id="3i0r8k"
Kimchi Fried Rice

Available:
✓ Kimchi
✓ Egg
✓ Soy Sauce

Missing:
✗ Rice
✗ Green Onion
✗ Sesame Oil
```

Missing ingredients should be usable by the shopping-list functionality.

### Shared Recommendation Logic

Both Guest ingredient selections and authenticated users' saved inventories shall use the same recommendation logic.

```text id="cq8ph5"
Guest Ingredients ──────────┐
                            │
                            ▼
                   RecommendationService
                            ▲
                            │
Saved User Inventory ───────┘
```

Additional filters such as allergies, dietary preferences, cuisine preferences, and other supported filters shall be applicable to both recommendation modes.

---

## FR-13 — Allergy and Dietary Filtering

Guests shall be able to provide supported allergy and dietary filters when searching for or requesting recipe recommendations.

Authenticated users shall additionally be able to save supported allergies and dietary preferences to their accounts.

Saved preferences should automatically apply to recipe recommendations and filtering where appropriate.

Recipes containing ingredients known by the system to conflict with selected allergy filters shall be excluded from normal recommendations or clearly identified according to the application's filtering rules.

The application shall not represent its allergy filtering as a substitute for professional medical or food-safety guidance.

---

## FR-14 — Saved Recipes

Authenticated users shall be able to save recipes to their accounts.

Users shall be able to:

- Save a recipe.
- View saved recipes.
- Remove a recipe from their saved recipes.

Saved recipe information shall persist across authenticated sessions.

Guest users are not required to have persistent saved recipe functionality.

---

## FR-15 — Recipe Reviews and Ratings

Guests shall be able to view recipe ratings and reviews.

Authenticated users shall be able to submit recipe ratings and reviews.

A review shall contain or reference:

- The associated authenticated user.
- The associated recipe.
- A rating.
- An optional written comment.
- A creation date.

Requiring authentication for review creation ensures that submitted reviews can be associated with an identifiable application account.

---

## FR-16 — Shopping List

Guests and authenticated users shall be able to generate a shopping list based on ingredients they are missing for selected recipes.

The system should compare required recipe ingredients against the ingredients currently provided by the user.

The system should identify ingredients required by the recipe that the user does not currently have.

Guests shall be able to use a generated shopping list during their current session.

Authenticated users shall additionally be able to persist and manage shopping lists across sessions.

Authenticated users shall be able to:

- Save shopping lists.
- View saved shopping lists.
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

Administrative functionality shall not be accessible to normal registered users or guests.

---

## FR-20 — Contact and Support

The system shall provide users with a method for submitting questions, feedback, or support requests.

---

# 4. Potential / Future Requirements

The following functionality is being considered but is not currently required for the core application.

## FUT-01 — AI-Generated Recipes

The system may allow users to generate new recipes based on available ingredients and user-provided instructions using an AI service.

## FUT-02 — AI Recipe Assistant

The system may provide a conversational assistant for recipe discovery and cooking-related questions.

## FUT-03 — Recipe Scanning

The system may allow users to upload or scan recipe information and automatically extract recipe and ingredient data.

## FUT-04 — Advanced Ingredient Tracking

The persistent ingredient inventory may eventually support additional information such as:

- Quantity.
- Measurement units.
- Expiration dates.
- Purchase dates.

## FUT-05 — Advanced Interface Customization

Authenticated users may eventually be able to customize additional aspects of the application interface.

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

Failure of optional functionality should not prevent users from accessing the application's core recipe discovery functionality.

---

## NFR-09 — Performance

The application should provide responsive interaction under the expected workload of the project.

Recipe search and recommendation operations should avoid unnecessary processing, database queries, and data transfer.

---

## NFR-10 — Usability

The application's core recipe discovery workflow should not require account creation.

Primary workflows such as:

- Entering available ingredients.
- Finding recipes.
- Viewing recommendations.
- Generating a shopping list.

should be easy to locate and use.

Account creation should primarily provide persistence, personalization, and functionality that requires user identity.

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

# 6. Core User Flow

The primary application workflow shall be accessible to both guests and authenticated users.

```text id="l03rzt"
Open Application
       │
       ▼
Enter Available Ingredients
       │
       ├── Select Allergies / Preferences / Filters
       │
       ▼
Get Recipe Recommendations
       │
       ▼
View Recipe
       │
       ├── View Required Ingredients
       ├── View Missing Ingredients
       └── View Instructions
       │
       ▼
Generate Shopping List
```

Authentication extends this workflow with persistent functionality:

```text id="twm0ml"
Guest Experience
       │
       ▼
Create Account / Log In
       │
       ▼
Persistent User Experience
       │
       ├── Saved Ingredient Inventory
       ├── Saved Recipes
       ├── Saved Shopping Lists
       ├── Saved Preferences / Allergies
       ├── Reviews / Ratings
       └── Personalized Dashboard
```

---

# 7. Core Project Scope

The initial implementation will prioritize:

1. Recipe browsing and display.
2. Ingredient input for guests and authenticated users.
3. Ingredient-based recipe recommendations.
4. Recipe search and filtering.
5. Allergy and dietary filtering.
6. Shopping list generation.
7. User registration and authentication.
8. Persistent ingredient inventory for authenticated users.
9. Saved recipes.
10. Persistent shopping lists.
11. User profile and saved preferences.
12. Personalized authenticated dashboard.
13. Reviews and ratings.
14. Manual recipe creation.
15. Recipe and user media support.
16. Basic administrative functionality.

AI functionality, recipe scanning, advanced inventory tracking, advanced interface customization, and other intelligent features are outside the committed initial scope.
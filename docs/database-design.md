# Database Design

## 1. Purpose

This document describes the relational data model for the Recipe Suggestion App.

The application will use PostgreSQL as its relational database.

The database design supports:

- Guest and registered-user recipe discovery.
- Persistent registered-user application accounts.
- Ingredient inventories.
- Recipes and recipe ingredients.
- Recipe recommendations.
- Saved recipes.
- Recipe classifications and user preferences.
- Allergies.
- Reviews and ratings.
- Shopping lists.
- Media references.
- Administrative functionality.

Guest-specific temporary state does not necessarily need to be stored in the persistent relational database.

Authentication credentials are managed by Amazon Cognito rather than stored directly in the application database.

---

# 2. Design Principles

## 2.1 Shared Domain Entities

Common concepts should be represented once and referenced by other entities.

For example, an ingredient should not be independently represented as plain text in every recipe, user inventory, and shopping list.

Instead:

```text
                     Ingredient
                    /     |     \
                   /      |      \
                  ▼       ▼       ▼
          InventoryItem   |   ShoppingListItem
                          |
                          ▼
                   RecipeIngredient
                          |
                          ▼
                       Recipe
```

This provides a consistent representation of ingredients throughout the application.

---

## 2.2 Normalize Core Application Data

The database should avoid unnecessary duplication of persistent information.

Relationships should be represented using foreign keys and relationship tables where appropriate.

For example, a recipe containing chicken should reference the existing canonical `Ingredient` representing chicken rather than creating an independent copy of `"Chicken"`.

Recipe classifications should similarly use shared `Tag` entities rather than repeatedly storing unrestricted classification text directly on recipes.

---

## 2.3 Separate Persistent and Temporary State

Registered-user information that must survive across sessions shall be stored persistently.

Guest information such as temporary ingredient selections, filters, or generated shopping lists does not necessarily need persistent database storage.

```text
Guest
  │
  └── Temporary State

Registered User
  │
  └── PostgreSQL Persistent State
```

Both may still use the same backend business services.

---

## 2.4 Separate Authentication Identity from Application Data

Amazon Cognito is responsible for authentication.

PostgreSQL stores application-specific user information and relationships.

```text
Amazon Cognito
      │
      │ authenticated identity
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

The application database shall not store or manage user passwords.

Each application user shall instead be associated with the corresponding Cognito identity through a stable external identifier.

---

# 3. Core Entities

The initial persistent data model contains the following major entities:

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

Additional entities may be introduced as requirements evolve.

---

# 4. High-Level Entity Relationships

```text
                         User
                          │
        ┌─────────┬───────┼──────────┬────────────┐
        │         │       │          │            │
        ▼         ▼       ▼          ▼            ▼
 UserProfile Inventory SavedRecipe Review   ShoppingList
                │         │         │            │
                ▼         ▼         ▼            ▼
           Ingredient   Recipe ───────── ShoppingListItem
                ▲         │                     │
                │         │                     ▼
                │    RecipeIngredient ───── Ingredient
                │         │
                └─────────┘

User ── UserAllergy ─────── Allergen
                              ▲
                              │
                         Ingredient

User ── UserPreference ── Tag ── Recipe
```

The major relationships are:

```text
User        M:N Ingredient   through InventoryItem
Recipe      M:N Ingredient   through RecipeIngredient

User        M:N Recipe       through SavedRecipe
User        M:N Recipe       through Review

User        M:N Allergen     through UserAllergy
Ingredient  M:N Allergen

User        M:N Tag          through UserPreference
Recipe      M:N Tag

User        1:N ShoppingList
ShoppingList 1:N ShoppingListItem
ShoppingListItem N:1 Ingredient
```

---

# 5. User

The `User` entity represents the application's persistent record for an authenticated user.

Amazon Cognito is responsible for authentication identity and authentication credentials.

The application database shall not store or manage user passwords.

Each application `User` shall be associated with the corresponding Amazon Cognito identity using a stable external identifier.

Conceptually:

```text
User
├── id
├── cognito_subject
├── account_status
├── is_admin / application permissions
├── created_at
└── updated_at
```

`cognito_subject` represents the stable identifier associated with the authenticated Cognito identity.

The exact Django representation of permissions may use appropriate Django authorization functionality, but authentication credentials remain managed by Cognito.

Relationship:

```text
Amazon Cognito Identity
          │
          │ stable external identifier
          ▼
         User
```

Application-specific data remains associated with the local `User` entity rather than being stored in Cognito.

---

# 6. User Profile

`UserProfile` stores supported application-specific user information that does not belong directly to authentication.

Conceptually:

```text
UserProfile
├── id
├── user_id
├── display_name
├── profile_image_reference
└── other supported profile settings
```

Relationship:

```text
User 1 ───────── 1 UserProfile
```

Each authenticated application user has at most one associated profile.

A profile image should reference external media storage rather than storing the image binary directly in PostgreSQL.

Dietary preferences, cuisine preferences, allergies, and similar structured information should use their corresponding relationship entities rather than being stored as unrestricted profile text.

---

# 7. Ingredient

`Ingredient` represents a canonical food ingredient recognized by the application.

The purpose of this entity is to provide a common ingredient representation that can be referenced by recipes, user inventories, shopping lists, allergy data, and recommendation logic.

Conceptually:

```text
Ingredient
├── id
├── name
└── category
```

Examples:

```text
1   Chicken Breast
2   White Rice
3   Egg
4   Cabbage
5   Kimchi
6   Soy Sauce
7   Garlic
8   Green Onion
```

Ingredient names should be standardized so recipes and user inventories can reference the same underlying ingredient.

Ingredient names should be unique where appropriate to prevent duplicate canonical ingredient records.

## 7.1 Canonical Ingredient Principle

Different descriptions of the same underlying food should resolve to the same canonical ingredient when the differences do not materially affect recipe usage.

For example:

```text
Tyson Frozen Chicken Breast ───┐
                               │
Frozen Chicken Breast ─────────┼──→ Chicken Breast
                               │
Fresh Chicken Breast ──────────┘
```

These descriptions may contain different product information, but they represent the same canonical ingredient for recipe matching:

```text
Ingredient
id: 1
name: Chicken Breast
category: Poultry
```

Product-specific properties such as brand, packaging, storage condition, purchase location, or purchase date should not normally create separate canonical ingredients unless the distinction materially affects recipe usage.

Ingredient normalization should not combine foods that have meaningfully different recipe uses.

For example:

```text
Chicken Breast
Chicken Thigh
Ground Chicken
Whole Chicken
```

These remain separate canonical ingredients even if they share a broader category such as `Poultry`.

Ingredient categories are organizational metadata and do not automatically imply that ingredients are interchangeable.

## 7.2 Ingredient Resolution

Guest-entered ingredient descriptions should be resolved to canonical ingredients before recommendation processing whenever possible.

For example:

```text
User Input
"Tyson Frozen Chicken Breast"
             │
             ▼
     Ingredient Resolution
             │
             ▼
Canonical Ingredient
      "Chicken Breast"
```

The recommendation system should compare canonical ingredients rather than arbitrary raw text whenever possible.

---

# 8. Inventory Item

`InventoryItem` represents an ingredient stored persistently in an authenticated user's inventory.

Conceptually:

```text
InventoryItem
├── id
├── user_id
├── ingredient_id
├── created_at
└── updated_at
```

Relationship:

```text
User 1 ─────── * InventoryItem * ─────── 1 Ingredient
```

For example:

```text
User #15
   │
   ├── InventoryItem ── Egg
   ├── InventoryItem ── Cabbage
   ├── InventoryItem ── Kimchi
   └── InventoryItem ── Soy Sauce
```

Each inventory item references a canonical `Ingredient`.

The combination of `user_id` and `ingredient_id` should be unique for the initial implementation:

```text
UNIQUE(user_id, ingredient_id)
```

This prevents duplicate entries for the same canonical ingredient within a user's inventory.

Guest ingredient selections do not require persistent `InventoryItem` records.

Guest ingredients should instead be resolved to the same canonical ingredient representation before recommendation processing.

```text
Guest Input
    │
    ▼
Ingredient Resolution
    │
    ▼
Canonical Ingredients
    │
    ▼
RecommendationService
```

Authenticated users obtain the same type of recommendation input through their saved inventory:

```text
User
 │
 ▼
InventoryItem
 │
 ▼
Ingredient
 │
 ▼
RecommendationService
```

This allows both Guests and authenticated users to use the same recommendation service.

## 8.1 Initial Quantity Handling

For the initial application, recommendation eligibility is primarily based on whether an ingredient is available rather than whether the user has an exact sufficient quantity.

For example:

```text
User has:
Egg

Recipe requires:
2 Eggs
```

The initial recommendation system may treat `Egg` as available without verifying that the user has at least two eggs.

Quantity, measurement units, purchase dates, and expiration dates may be introduced later as extended inventory features without changing the core ingredient relationship.

---

# 9. Recipe

`Recipe` represents a recipe available through the application.

Conceptually:

```text
Recipe
├── id
├── owner_id
├── name
├── description
├── instructions
├── preparation_time
├── cooking_time
├── image_reference
├── created_at
└── updated_at
```

`owner_id` references the authenticated application user who created and owns the recipe.

Recipe classifications such as cuisine, dietary classification, cost level, and other supported categories are represented through the recipe's relationship with `Tag` rather than duplicated as fields directly on `Recipe`.

Recipe ingredients are represented through `RecipeIngredient`, which references canonical `Ingredient` entities.

Recipe images should be stored in external media storage, with the database maintaining the information necessary to reference the image.

Recipe ownership may be used by backend authorization rules to determine whether a user is allowed to modify or delete a recipe.

Administrators may receive broader recipe-management permissions independent of ownership.

---

# 10. Recipe Ingredient

`RecipeIngredient` represents the relationship between a recipe and a canonical ingredient.

Recipes and ingredients have a many-to-many relationship. A recipe contains multiple ingredients, and an ingredient may appear in multiple recipes.

Because this relationship also contains recipe-specific information such as quantity, unit, optional status, and preparation notes, it is represented using an intermediate entity.

```text
Recipe
   │
   ▼
RecipeIngredient
   │
   ▼
Ingredient
```

Conceptually:

```text
RecipeIngredient
├── id
├── recipe_id
├── ingredient_id
├── quantity
├── unit
├── is_optional
└── notes
```

Example:

```text
Chicken Fried Rice

RecipeIngredient
├── Chicken Breast    200 g      required
├── White Rice        2 cups     required
├── Egg               2          required
├── Garlic            2 cloves   required
├── Soy Sauce         2 tbsp     required
└── Green Onion       1 stalk    optional
```

`is_optional` indicates whether the ingredient is required for recipe eligibility.

Optional ingredients shall not prevent a recipe from qualifying for the `AVAILABLE_ONLY` recommendation mode.

`notes` may contain recipe-specific preparation information such as:

```text
"finely chopped"
"divided"
"room temperature"
"for garnish"
```

These descriptions should not create separate canonical ingredients.

For example:

```text
Ingredient:
Chicken Breast

RecipeIngredient.notes:
"cut into thin strips"
```

rather than creating an ingredient named:

```text
Chicken Breast Cut Into Thin Strips
```

A recipe should not contain duplicate `RecipeIngredient` relationships for the same canonical ingredient unless the implementation has a specific reason to represent separate uses.

The combination should therefore normally be unique:

```text
UNIQUE(recipe_id, ingredient_id)
```

This relationship is central to recipe matching and shopping-list generation.

---

# 11. Saved Recipe

Authenticated users shall be able to save recipes.

This creates a many-to-many relationship:

```text
User
  │
  ▼
SavedRecipe
  │
  ▼
Recipe
```

Conceptually:

```text
SavedRecipe
├── id
├── user_id
├── recipe_id
└── created_at
```

A user should not save the same recipe multiple times.

Therefore:

```text
UNIQUE(user_id, recipe_id)
```

Guest users do not require persistent `SavedRecipe` records.

---

# 12. Review

`Review` represents a rating or review submitted by an authenticated user for a recipe.

Conceptually:

```text
Review
├── id
├── user_id
├── recipe_id
├── rating
├── comment
├── created_at
└── updated_at
```

Relationships:

```text
User 1 ─────── * Review

Recipe 1 ───── * Review
```

A review belongs to one authenticated user and one recipe.

The initial design shall allow at most one active review from a user for a particular recipe:

```text
UNIQUE(user_id, recipe_id)
```

A user may update their existing review rather than creating multiple independent reviews for the same recipe.

The backend should validate that ratings fall within the supported rating range.

---

# 13. Allergen

Allergens are represented independently from recipe tags.

Conceptually:

```text
Allergen
├── id
└── name
```

Examples:

```text
Peanut
Tree Nut
Milk
Egg
Wheat
Soy
Fish
Shellfish
Sesame
```

Allergen names should use standardized values where practical.

Ingredients may be associated with one or more allergens.

```text
Ingredient * ───── * Allergen
```

For example:

```text
Peanut Butter
      │
      └── Peanut
```

A recipe's allergen information can therefore be determined through its ingredients:

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

This allows allergen information to be derived from canonical ingredient relationships instead of relying only on manually assigned recipe labels.

---

# 14. User Allergy

`UserAllergy` represents an authenticated user's saved allergy information.

Conceptually:

```text
UserAllergy
├── id
├── user_id
└── allergen_id
```

Relationship:

```text
User
 │
 ▼
UserAllergy
 │
 ▼
Allergen
```

The combination should be unique:

```text
UNIQUE(user_id, allergen_id)
```

This allows recommendation and filtering logic to compare recipe ingredients against a user's recorded allergens.

Guest allergy selections may use the same standardized `Allergen` values temporarily without requiring persistent `UserAllergy` records.

---

# 15. Recipe Classification and Tags

Recipes use a flexible tag-based classification system.

A `Tag` represents a standardized descriptive property of a recipe, such as cuisine, dietary classification, cost level, or another supported category.

Conceptually:

```text
Tag
├── id
├── name
└── type
```

Initial tag types:

```text
DIET
CUISINE
COST
OTHER
```

Examples:

| Name | Type |
|---|---|
| Vegan | DIET |
| Vegetarian | DIET |
| Halal | DIET |
| Korean | CUISINE |
| Vietnamese | CUISINE |
| Italian | CUISINE |
| Cheap | COST |
| Moderate | COST |
| Expensive | COST |
| Quick | OTHER |
| High Protein | OTHER |

Recipes and Tags have a many-to-many relationship:

```text
Recipe
   │
   │ M:N
   ▼
Tag
```

Example:

```text
Kimchi Fried Rice

Tags:
- Korean
- Halal
- Cheap
- Quick
```

This allows additional classifications to be introduced without modifying the `Recipe` model for every new category.

A tag should normally be unique within its type:

```text
UNIQUE(name, type)
```

For example, there should not normally be two separate `Korean` tags with type `CUISINE`.

## 15.1 Tags vs. Allergens

Tags describe recipe characteristics.

Allergens remain associated with canonical Ingredients rather than being represented only as recipe Tags.

```text
                       Recipe
                      /      \
                     /        \
                    ▼          ▼
           RecipeIngredient    Tag
                    │           │
                    ▼           ├── DIET
               Ingredient       ├── CUISINE
                    │           ├── COST
                    ▼           └── OTHER
                Allergen
```

For example, a manually assigned `Peanut-Free` label should not be treated as the authoritative source for allergy filtering.

Structured Ingredient → Allergen relationships provide the authoritative application relationship used for allergen filtering.

---

# 16. User Preference

`UserPreference` represents a standardized recipe preference saved by an authenticated user.

It uses the same `Tag` entities used to classify recipes.

Conceptually:

```text
UserPreference
├── id
├── user_id
└── tag_id
```

Relationship:

```text
User
 │
 ▼
UserPreference
 │
 ▼
Tag
 │
 ▼
Recipe
```

Examples:

```text
User #15

Preferences:
- Vegan       [DIET]
- Vietnamese  [CUISINE]
- Cheap       [COST]
```

The combination should be unique:

```text
UNIQUE(user_id, tag_id)
```

Using shared `Tag` entities allows user preferences and recipe classifications to use the same standardized vocabulary.

For example:

```text
User Preference
Vietnamese [CUISINE]
       │
       ▼
      Tag
       ▲
       │
Recipe Classification
Vietnamese [CUISINE]
```

Guest users may select temporary dietary, cuisine, cost, or other supported filters without creating persistent `UserPreference` records.

The exact business rules used to determine whether a recipe qualifies for classifications such as `Halal` are separate from the relational database structure.

---

# 17. Shopping List

A registered user may maintain one or more persistent shopping lists.

Conceptually:

```text
ShoppingList
├── id
├── user_id
├── name
├── created_at
└── updated_at
```

Relationship:

```text
User 1 ───── * ShoppingList
```

Each persistent shopping list belongs to one authenticated user.

Guest-generated shopping lists do not require persistent `ShoppingList` records.

---

# 18. Shopping List Item

A shopping list contains one or more shopping-list items.

Conceptually:

```text
ShoppingListItem
├── id
├── shopping_list_id
├── ingredient_id
├── quantity
├── unit
├── completed
└── created_at
```

Relationship:

```text
ShoppingList
      │
      ▼
ShoppingListItem
      │
      ▼
Ingredient
```

For example:

```text
Shopping List

☐ Chicken Breast
☐ Green Onion
☑ Soy Sauce
```

Each shopping-list item references the same canonical `Ingredient` entities used by recipes and inventories.

Guest-generated shopping lists may use the same conceptual item structure without being stored persistently.

---

# 19. Recommendation Data Flow

Recipe recommendations do not require a persistent `Recommendation` database entity for the initial implementation.

The recommendation service calculates recommendations dynamically using canonical ingredient relationships.

Both Guests and authenticated users use the same recommendation logic:

```text
Guest Ingredients ────────────┐
                              │
                              ▼
                     RecommendationService
                              ▲
                              │
Saved User Inventory ─────────┘
```

The difference is the source and persistence of ingredient data, not the recommendation algorithm.

Additional supported filters may use standardized Tags and Allergens.

Conceptually:

```text
Canonical Ingredients
        │
        ├── User / Guest Filters
        │       ├── Tags
        │       └── Allergens
        │
        ▼
RecommendationService
        │
        ▼
Matching Recipes
```

## 19.1 Recommendation Mode: Available Ingredients Only

In `AVAILABLE_ONLY` mode, a recipe is eligible when every required recipe ingredient is available to the user.

The recipe does not need to use every ingredient the user has.

Conceptually:

```text
Required Recipe Ingredients ⊆ User Ingredients
```

Example:

```text
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

Optional `RecipeIngredient` records do not determine eligibility for this mode.

## 19.2 Recommendation Mode: Partial Ingredient Match

In `PARTIAL_MATCH` mode, a recipe may require ingredients that the user does not currently have.

A recipe is eligible when at least one required recipe ingredient overlaps with the user's available ingredients.

Conceptually:

```text
Required Recipe Ingredients ∩ User Ingredients ≠ ∅
```

The service should identify ingredients the user already has and ingredients that are missing.

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

Eligible recipes should be ranked according to how well they match the user's available ingredients.

A simple initial match score may be calculated as:

```text
              Available Required Ingredients
Match Score = ------------------------------
                Total Required Ingredients
```

For example:

```text
Available Required Ingredients = 3
Total Required Ingredients     = 5

Match Score = 3 / 5 = 60%
```

The scoring method may be refined later without changing the underlying ingredient relationships.

## 19.3 Recommendation Results

The recommendation process should be capable of producing:

```text
RecommendationResult
├── recipe
├── match_score
├── available_ingredients
├── missing_ingredients
└── optional_missing_ingredients
```

Missing ingredients can then be passed directly to shopping-list functionality.

Recommendation results do not need to be stored persistently unless future requirements introduce recommendation history, analytics, or caching.

---

# 20. Shopping List Generation

Shopping-list generation uses the same canonical ingredient data used by inventory, recipes, and recommendation logic.

Conceptually:

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

For a Guest, the generated list may remain temporary.

For an authenticated user, the resulting items may be persisted to a `ShoppingList`.

Because missing ingredients are already represented as canonical `Ingredient` entities, shopping-list generation can reuse those entities directly.

---

# 21. Media References

Media binaries shall not be stored directly in PostgreSQL.

The database stores references associated with application entities.

Conceptually:

```text
Recipe
├── database information
└── image_reference ──────────→ Media Storage

UserProfile
├── database information
└── profile_image_reference ──→ Media Storage
```

Detailed media-storage implementation is documented in `aws-architecture.md`.

---

# 22. Data Integrity and Uniqueness Constraints

The database should enforce important relationship constraints where practical.

Initial constraints include:

```text
Ingredient
UNIQUE(name)

User
UNIQUE(cognito_subject)

InventoryItem
UNIQUE(user_id, ingredient_id)

RecipeIngredient
UNIQUE(recipe_id, ingredient_id)

SavedRecipe
UNIQUE(user_id, recipe_id)

Review
UNIQUE(user_id, recipe_id)

UserAllergy
UNIQUE(user_id, allergen_id)

Tag
UNIQUE(name, type)

UserPreference
UNIQUE(user_id, tag_id)
```

Foreign-key relationships should preserve referential integrity.

Deletion behavior should be selected deliberately during Django model implementation.

For example, deleting a user should not accidentally delete globally shared canonical Ingredients or Tags.

---

# 23. Relationship Summary

```text
Amazon Cognito
      │
      │ authenticated identity
      ▼
     User
      │
      ├──── 1 UserProfile
      │
      ├──── * InventoryItem ───── Ingredient
      │
      ├──── * SavedRecipe ─────── Recipe
      │
      ├──── * Review ──────────── Recipe
      │
      ├──── * UserAllergy ─────── Allergen
      │
      ├──── * UserPreference ──── Tag
      │
      └──── * ShoppingList
                    │
                    └──── * ShoppingListItem ───── Ingredient


Recipe
  │
  ├──── owner ────────────────── User
  │
  ├──── * RecipeIngredient ───── Ingredient
  │
  ├──── * Tag
  │
  └──── * Review


Ingredient
  │
  └──── * Allergen


Tag
  │
  ├──── * Recipe
  └──── * UserPreference
```

The canonical `Ingredient` entity acts as the common reference point across inventory, recipe, recommendation, allergen, and shopping-list functionality.

The canonical `Tag` entity acts as the common vocabulary between recipe classification and persistent user preferences.

---

# 24. Entity Summary

The initial persistent database model contains:

| Entity | Purpose |
|---|---|
| `User` | Application user associated with a Cognito identity |
| `UserProfile` | Additional application profile information |
| `Ingredient` | Canonical standardized ingredient |
| `InventoryItem` | User-to-Ingredient inventory relationship |
| `Recipe` | Core recipe information and ownership |
| `RecipeIngredient` | Recipe-to-Ingredient relationship with recipe-specific information |
| `SavedRecipe` | User-to-saved-Recipe relationship |
| `Tag` | Standardized `DIET`, `CUISINE`, `COST`, or `OTHER` classification |
| `UserPreference` | User-to-Tag saved preference relationship |
| `Allergen` | Standardized allergen |
| `UserAllergy` | User-to-Allergen relationship |
| `Review` | User rating/review associated with a Recipe |
| `ShoppingList` | Persistent shopping list belonging to a User |
| `ShoppingListItem` | Canonical Ingredient within a ShoppingList |

The initial design does **not** require persistent database entities for:

```text
Guest sessions
Recommendation results
Temporary Guest ingredient selections
Temporary Guest filters
Temporary Guest shopping lists
```

These may remain application/session state unless future requirements introduce persistence, analytics, caching, or other needs.

---

# 25. Core Design Summary

The major database design principles can be summarized as:

```text
Amazon Cognito
      │
      │ authentication identity
      ▼
Application User
      │
      └── PostgreSQL application data


Ingredient
      │
      ├── Inventory
      ├── Recipes
      ├── Allergens
      ├── Recommendations
      └── Shopping Lists


Tag
      │
      ├── Recipe Classification
      └── User Preferences


Allergen
      │
      ├── Ingredient Relationships
      └── User Allergy Relationships


RecommendationService
      │
      └── Dynamic calculation
          No persistent Recommendation entity required initially
```

This structure ensures that:

- Authentication credentials remain separate from application data.
- Ingredients use one canonical representation throughout the system.
- Recipe classifications and user preferences use the same standardized Tag vocabulary.
- Allergens remain structured around Ingredient relationships rather than relying only on manually assigned recipe labels.
- Guest and authenticated users can share the same recommendation logic.
- Persistent data remains normalized and reusable across application features.

---

# 26. Related Documentation

```text
requirements.md
    ↓
What data does the application need?

database-design.md
    ↓
How is that data represented and related?

api-design.md
    ↓
How is that data accessed?

system-design.md
    ↓
How does application logic use it?

aws-architecture.md
    ↓
Where is the data and application infrastructure hosted?
```
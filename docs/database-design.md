# Database Design

## 1. Purpose

This document describes the proposed relational data model for the Recipe Suggestion App.

The application will use PostgreSQL as its relational database.

The database design aims to support:

- Guest and registered-user recipe discovery.
- Persistent registered-user accounts.
- Ingredient inventories.
- Recipes and recipe ingredients.
- Recipe recommendations.
- Saved recipes.
- Dietary preferences and allergies.
- Reviews and ratings.
- Shopping lists.
- Media references.
- Administrative functionality.

Guest-specific temporary state does not necessarily need to be stored in the persistent relational database.

---

# 2. Design Principles

## 2.1 Shared Domain Entities

Common concepts should be represented once and referenced by other entities.

For example, an ingredient should not be independently represented as plain text in every recipe and user inventory.

Instead:

```text
                     Ingredient
                    /          \
                   /            \
                  ▼              ▼
          InventoryItem    RecipeIngredient
                │                 │
                ▼                 ▼
              User             Recipe
```

This provides a consistent representation of ingredients throughout the application.

---

## 2.2 Normalize Core Application Data

The database should avoid unnecessary duplication of persistent information.

Relationships should be represented using foreign keys and relationship tables where appropriate.

For example, a recipe containing chicken should reference the existing `Ingredient` representing chicken rather than creating a new independent copy of `"Chicken"`.

---

## 2.3 Separate Persistent and Temporary State

Registered-user information that must survive across sessions shall be stored persistently.

Guest information such as temporary ingredient selections or generated shopping lists does not necessarily need persistent database storage.

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

# 3. Core Entities

The initial data model contains the following major entities:

```text
User
UserProfile

Ingredient
InventoryItem

Recipe
RecipeIngredient
SavedRecipe

Allergen
UserAllergy

DietaryPreference
UserDietaryPreference

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
             ┌────────────┼─────────────┐
             │            │             │
             ▼            ▼             ▼
        UserProfile  InventoryItem   SavedRecipe
                          │             │
                          ▼             ▼
                     Ingredient       Recipe
                          ▲             │
                          │             ▼
                          └──── RecipeIngredient
                                        │
                                        ▼
                                   Ingredient


User ───────── Review ───────── Recipe

User ───── ShoppingList
                │
                ▼
        ShoppingListItem
                │
                ▼
           Ingredient
```

Additional preference and allergy relationships connect the user to supported dietary and allergen data.

---

# 5. User

The `User` entity represents an authenticated application account.

Authentication-related information will be managed through the selected Django authentication implementation.

Conceptually, a user may contain information such as:

```text
User
├── id
├── username / email
├── password authentication information
├── account status
├── administrative permissions
├── created_at
└── updated_at
```

The exact authentication fields will depend on the authentication design.

The application should use Django's authentication framework rather than implementing password storage manually.

---

# 6. User Profile

`UserProfile` stores supported user information that does not directly belong to authentication.

Conceptually:

```text
UserProfile
├── id
├── user_id
├── display_name
├── profile_image
└── other supported profile settings
```

Relationship:

```text
User 1 ───────── 1 UserProfile
```

A profile image should reference external media storage rather than storing the image binary directly in PostgreSQL.

Whether a separate `UserProfile` model is required will be finalized during Django model design.

---

# 7. Ingredient

`Ingredient` represents a standardized ingredient known by the application.

Conceptually:

```text
Ingredient
├── id
├── name
├── category
└── other supported metadata
```

Examples:

```text
1   Chicken Breast
2   White Rice
3   Egg
4   Garlic
5   Onion
6   Soy Sauce
```

Ingredient names should be sufficiently standardized so recipes and user inventories can reference the same underlying ingredient.

For example:

```text
User Inventory
"Egg"
   │
   ▼
Ingredient #3


Recipe
"2 Eggs"
   │
   ▼
Ingredient #3
```

This common reference is important for recipe matching.

---

# 8. Inventory Item

`InventoryItem` represents an ingredient stored in a registered user's persistent inventory.

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
   ├── InventoryItem ── Chicken
   ├── InventoryItem ── Rice
   ├── InventoryItem ── Egg
   └── InventoryItem ── Garlic
```

Advanced fields such as quantity, units, purchase date, and expiration date may be introduced later.

Guest ingredient selections do not require `InventoryItem` records.

---

# 9. Recipe

`Recipe` represents a recipe available through the application.

Conceptually:

```text
Recipe
├── id
├── name
├── description
├── instructions
├── preparation_time
├── cooking_time
├── cuisine
├── estimated_cost / cost_category
├── image
├── created_by
├── created_at
└── updated_at
```

`created_by` may reference the authenticated user who created the recipe where applicable.

Recipe images should be stored in external media storage, with the database maintaining the information necessary to reference the image.

---

# 10. Recipe Ingredient

Recipes and ingredients have a many-to-many relationship.

A recipe contains multiple ingredients, and an ingredient may appear in multiple recipes.

Because the relationship also contains information such as quantity and measurement unit, it should be represented using an intermediate entity.

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
└── optional
```

Example:

```text
Chicken Fried Rice

RecipeIngredient
├── Chicken Breast    200 g
├── White Rice        2 cups
├── Egg               2
├── Garlic            2 cloves
└── Soy Sauce         2 tbsp
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

A uniqueness constraint should prevent the same user from saving the same recipe multiple times unnecessarily.

---

# 12. Reviews

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

The system may restrict each user to one active review per recipe.

---

# 13. Allergens

Allergens should be represented independently from recipes.

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

Ingredients may be associated with one or more allergens.

Conceptually:

```text
Ingredient * ───── * Allergen
```

For example:

```text
Peanut Butter
      │
      └── Peanut
```

User allergy information can then reference the same allergen entities:

```text
User
 │
 ▼
UserAllergy
 │
 ▼
Allergen
```

Conceptually:

```text
UserAllergy
├── id
├── user_id
└── allergen_id
```

This allows recommendation filtering to compare recipe ingredients against a user's recorded allergens.

---

# 14. Dietary Preferences

Supported dietary classifications should use standardized values rather than arbitrary text where practical.

Examples may include:

```text
Vegan
Vegetarian
Halal
```

Conceptually:

```text
DietaryPreference
├── id
├── name
└── description
```

Registered users may save preferences:

```text
User
 │
 ▼
UserDietaryPreference
 │
 ▼
DietaryPreference
```

Recipes may also be associated with supported dietary classifications.

```text
Recipe * ───── * DietaryPreference
```

This allows recipe filtering to compare recipe classifications against user preferences.

The exact rules used to assign dietary classifications such as halal will be defined separately from the database schema.

---

# 15. Shopping List

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

---

# 16. Shopping List Item

A shopping list contains one or more shopping list items.

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

Guest-generated shopping lists may use the same conceptual item structure without being stored persistently.

---

# 17. Recommendation Data Flow

Recipe recommendations do not require a persistent `Recommendation` database entity for the initial implementation.

The recommendation service can calculate recommendations dynamically.

```text
Guest Ingredients ────────────┐
                              │
                              ▼
                     RecommendationService
                              ▲
                              │
Saved User Inventory ─────────┘
                              │
                              ▼
                     RecipeIngredient
                              │
                              ▼
                          Recipes
```

For example:

```text
Available:

Chicken
Rice
Egg
Garlic

          ↓

RecommendationService

          ↓

Recipe A
4 / 4 ingredients available

Recipe B
4 / 5 ingredients available

Recipe C
3 / 5 ingredients available
```

Recommendation results do not need to be stored unless future requirements introduce recommendation history, analytics, or caching.

---

# 18. Shopping List Generation

Shopping-list generation uses the same standardized ingredient data.

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

For a guest, the generated list may remain temporary.

For an authenticated user, the resulting items may be persisted to a `ShoppingList`.

---

# 19. Media References

Media binaries shall not be stored directly in PostgreSQL.

The database stores references associated with application entities.

Conceptually:

```text
Recipe
├── database information
└── image reference ───────────→ Media Storage

UserProfile
├── database information
└── avatar reference ──────────→ Media Storage
```

Detailed storage implementation is documented in `aws-architecture.md`.

---

# 20. Initial Relationship Summary

```text
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
 ├──── * UserDietaryPreference ── DietaryPreference
 │
 └──── * ShoppingList
              │
              └──── * ShoppingListItem ───── Ingredient


Recipe
 │
 ├──── * RecipeIngredient ───── Ingredient
 │
 ├──── * Review
 │
 └──── * DietaryPreference


Ingredient
 │
 └──── * Allergen
```

---

# 21. Proposed Entity List

The initial persistent database model is expected to contain:

| Entity | Purpose |
| --- | --- |
| User | Authentication and account identity |
| UserProfile | Additional profile information |
| Ingredient | Standardized ingredient |
| InventoryItem | Ingredient belonging to a user's inventory |
| Recipe | Recipe information |
| RecipeIngredient | Recipe-to-ingredient relationship |
| SavedRecipe | User-to-saved-recipe relationship |
| Review | User recipe rating/review |
| Allergen | Standardized allergen |
| UserAllergy | User-to-allergen relationship |
| DietaryPreference | Supported dietary classification |
| UserDietaryPreference | User-to-dietary-preference relationship |
| ShoppingList | Persistent user shopping list |
| ShoppingListItem | Ingredient within a shopping list |

This entity list may change as requirements and implementation details are refined.

---

# 22. Related Documentation

```text
requirements.md
    ↓
What data does the application need?

database-design.md
    ↓
How is that data related?

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
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

**---**

# 2. Design Principles

## 2.1 Shared Domain Entities

Common concepts should be represented once and referenced by other entities.

For example, an ingredient should not be independently represented as plain text in every recipe and user inventory.

Instead:

```text

                     Ingredient

                    /          \\

                   /            \\

                  ▼              ▼

          InventoryItem    RecipeIngredient

                │                 │

                ▼                 ▼

              User             Recipe

```

This provides a consistent representation of ingredients throughout the application.

**---**

## 2.2 Normalize Core Application Data

The database should avoid unnecessary duplication of persistent information.

Relationships should be represented using foreign keys and relationship tables where appropriate.

For example, a recipe containing chicken should reference the existing `Ingredient` representing chicken rather than creating a new independent copy of `"Chicken"`.

**---**

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

**---**

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

**---**

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

**---**

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

**---**

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

**---**

# 7. Ingredient

`Ingredient` represents a canonical food ingredient recognized by the application.

The purpose of this entity is to provide a common ingredient representation that can be referenced by recipes, user inventories, shopping lists, allergy data, and recommendation logic.

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
4   Cabbage
5   Kimchi
6   Soy Sauce
7   Garlic
8   Green Onion
```

Ingredient names should be standardized so that recipes and user inventories can reference the same underlying ingredient.

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

Ingredient normalization should not combine foods that may have meaningfully different recipe uses. For example:

```text
Chicken Breast
Chicken Thigh
Ground Chicken
Whole Chicken
```

These should remain separate canonical ingredients, even if they share a broader category such as `Poultry`.

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

Guest ingredient selections do not require persistent `InventoryItem` records. Guest ingredients should instead be resolved to the same canonical ingredient representation before recommendation processing.

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

This allows both guests and authenticated users to use the same recommendation service.

## 8.1 Initial Quantity Handling

For the initial application, recommendation eligibility will primarily be based on whether an ingredient is available rather than whether the user has an exact sufficient quantity.

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

`RecipeIngredient` represents the relationship between a recipe and a canonical ingredient.

Recipes and ingredients have a many-to-many relationship. A recipe contains multiple ingredients, and an ingredient may appear in multiple recipes.

Because this relationship also contains recipe-specific information such as quantity, unit, optional status, and preparation notes, it should be represented using an intermediate entity.

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
├── optional
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

The `optional` field indicates whether an ingredient is required for recipe eligibility.

Optional ingredients shall not prevent a recipe from qualifying for the `AVAILABLE_ONLY` recommendation mode.

The `notes` field may contain recipe-specific preparation information such as:

```text
"finely chopped"
"divided"
"room temperature"
"for garnish"
```

These descriptions should not create separate canonical ingredients. For example:

```text
Ingredient:
Chicken Breast

RecipeIngredient.notes:
"cut into thin strips"
```

rather than creating an ingredient named `Chicken Breast Cut Into Thin Strips`.

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

**---**

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

**---**

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

**---**

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

**---**

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

**---**

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

**---**

# 17. Recommendation Data Flow

Recipe recommendations do not require a persistent `Recommendation` database entity for the initial implementation.

The recommendation service shall calculate recommendations dynamically using canonical ingredient relationships.

Both guests and authenticated users shall use the same recommendation logic:

```text
Guest Ingredients ────────────┐
                              │
                              ▼
                     RecommendationService
                              ▲
                              │
Saved User Inventory ─────────┘
```

The difference is the source and persistence of the ingredient data, not the recommendation algorithm.

## 17.1 Recommendation Mode: Available Ingredients Only

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

## 17.2 Recommendation Mode: Partial Ingredient Match

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
Match Score = Available Required Ingredients
              ------------------------------
               Total Required Ingredients
```

For example:

```text
Available Required Ingredients = 3
Total Required Ingredients     = 5

Match Score = 3 / 5 = 60%
```

The scoring method may be refined later without changing the underlying ingredient relationships.

## 17.3 Recommendation Results

The recommendation process should be capable of producing:

```text
RecommendationResult
├── recipe
├── match_score
├── available_ingredients
├── missing_ingredients
└── optional_missing_ingredients
```

Missing ingredients can then be passed to shopping-list functionality.

Recommendation results do not need to be stored persistently unless future requirements introduce recommendation history, analytics, or caching.

---

# 18. Shopping List Generation

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

For a guest, the generated list may remain temporary.

For an authenticated user, the resulting items may be persisted to a `ShoppingList`.

**---**

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

**---**

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

**---**

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

**---**

# 22. Ingredient and Recommendation Design Summary

The canonical `Ingredient` entity acts as the common reference point across the application's inventory, recipe, recommendation, and shopping-list functionality.

```text
                         Ingredient
                        /    |     \
                       /     |      \
                      ▼      ▼       ▼
             InventoryItem   |   ShoppingListItem
                      │      |
                      │      ▼
                      │ RecipeIngredient
                      │      │
                      ▼      ▼
                    User   Recipe
```

This design allows both guest-entered ingredients and authenticated users' saved inventories to be converted into the same canonical ingredient representation and processed by the same `RecommendationService`.

The initial recommendation implementation supports:

- `AVAILABLE_ONLY`: all required recipe ingredients must be available.
- `PARTIAL_MATCH`: at least one required recipe ingredient must be available, and missing ingredients are identified.
- Optional ingredients do not prevent `AVAILABLE_ONLY` eligibility.
- Ingredient availability is initially matched by presence rather than exact inventory quantity.
- Missing canonical ingredients can be reused directly by shopping-list generation.

---

# 23. Related Documentation

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

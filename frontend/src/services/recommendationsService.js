import apiClient from "./api/apiClient";
import withAuth from "./devAuth";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

const recipesPath = (pageSize) =>
    `/recipes/?${new URLSearchParams({ page: "1", page_size: String(pageSize) })}`;

/**
 * A recommendation result as a recipe card object plus `match`.
 *
 * Results only carry { id, name, image } for the recipe, so the other fields
 * RecipeCard gets from the recipe list are filled with empty values.
 */
function toRecipeWithMatch(result) {
    const have = result.available_ingredients?.length ?? 0;
    const missing = result.missing_ingredients ?? [];

    return {
        description: "",
        tags: [],
        ...result.recipe,
        match: {
            have,
            total: have + missing.length,
            missing: missing.map((ingredient) => ingredient.name),
        },
    };
}

/**
 * Recipe feeds for the homepage.
 *
 *   POST /api/recommendations/?page_size=N
 *        { use_saved_inventory: true, match_mode: "PARTIAL_MATCH" }
 *     -> { results: [{ recipe: { id, name, image }, match_score,
 *                      available_ingredients, missing_ingredients,
 *                      optional_missing_ingredients }] }
 *
 * The backend (#6) reads the signed-in user's saved ingredients, leaves out
 * recipes with their saved allergens, and ranks by their saved preferences.
 */
const recommendationsService = {
    /**
     * Signed-in user: recipes that use their saved ingredients, best match
     * first. Each item has `match: { have, total, missing }`. Empty when
     * nothing matches, e.g. no ingredients saved yet.
     */
    async getRecommendationsForUser({ pageSize = 6, signal } = {}) {
        const params = new URLSearchParams({ page_size: String(pageSize) });

        const data = await apiClient.post(
            `/recommendations/?${params}`,
            { use_saved_inventory: true, match_mode: "PARTIAL_MATCH" },
            withAuth({ signal })
        );

        return toList(data).map(toRecipeWithMatch);
    },

    /** Signed-in user: recipe list; backend applies their saved preferences. */
    async getRecipesForUser({ pageSize = 6, signal } = {}) {
        const data = await apiClient.get(
            recipesPath(pageSize),
            withAuth({ signal })
        );

        return toList(data);
    },

    /** Guests: unfiltered recipes. */
    async getGeneralRecipes({ pageSize = 6, signal } = {}) {
        const data = await apiClient.get(recipesPath(pageSize), { signal });

        return toList(data);
    },
};

export default recommendationsService;

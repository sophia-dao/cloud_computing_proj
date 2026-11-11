import apiClient from "./api/apiClient";
import withAuth from "./devAuth";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

const recipesPath = (pageSize) =>
    `/recipes/?${new URLSearchParams({ page: "1", page_size: String(pageSize) })}`;

/**
 * Recipe feeds for the homepage.
 *
 * TODO(#6): the ingredient-matching engine (POST /api/recommendations/) is
 * not implemented on the backend yet. Until it is, "Recipes for You" uses
 * GET /api/recipes/, which already merges the signed-in user's saved tag
 * preferences into its filters (see apps/recipes/filters.py,
 * apply_user_defaults). Swap the body of getRecipesForUser() for the
 * recommendations call when #6 lands; callers will not need to change.
 */
const recommendationsService = {
    /** Signed-in user: backend applies their saved preferences. */
    async getRecipesForUser({ pageSize = 6, signal } = {}) {
        const data = await apiClient.get(
            recipesPath(pageSize),
            withAuth({ signal })
        );

        return toList(data);
    },

    /** Guests / users without preferences: unfiltered recipes. */
    async getGeneralRecipes({ pageSize = 6, signal } = {}) {
        const data = await apiClient.get(recipesPath(pageSize), { signal });

        return toList(data);
    },
};

export default recommendationsService;

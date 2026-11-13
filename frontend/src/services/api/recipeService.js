import apiClient from "./apiClient";

/**
 * Recipe submission (Issue #67).
 *
 *   POST /api/recipes/                       create (signed in; owner = you)
 *   GET  /api/recipes/duplicates/?name=...   same-name recipes, for a warning
 *   POST /api/recipes/{id}/image/            multipart "image" (owner or admin)
 *
 * Saved recipes (Issue #14), always the signed-in user's own:
 *   GET    /api/saved-recipes/[?recipe_id=]  { count, next, previous, results: [{ id, recipe, created_at }] }
 *   POST   /api/saved-recipes/               { recipe_id }  (201 new, 200 already saved)
 *   DELETE /api/saved-recipes/{id}/          id is the saved entry's id, not the recipe's
 */
const recipeService = {
    createRecipe(recipe, { signal } = {}) {
        return apiClient.post("/recipes/", recipe, { signal });
    },

    /** Existing recipes with the same name (case and extra spaces ignored). */
    async findRecipesWithSameName(name, { signal } = {}) {
        const params = new URLSearchParams({ name });
        const data = await apiClient.get(`/recipes/duplicates/?${params}`, { signal });

        return Array.isArray(data?.matches) ? data.matches : [];
    },

    getSavedRecipes({ page = 1, signal } = {}) {
        const params = new URLSearchParams({ page: String(page) });

        return apiClient.get(`/saved-recipes/?${params}`, { signal });
    },

    /** Your saved entry for one recipe, or null if you haven't saved it. */
    async findSavedRecipe(recipeId, { signal } = {}) {
        const params = new URLSearchParams({ recipe_id: String(recipeId) });
        const data = await apiClient.get(`/saved-recipes/?${params}`, { signal });

        return data?.results?.[0] ?? null;
    },

    saveRecipe(recipeId, { signal } = {}) {
        return apiClient.post("/saved-recipes/", { recipe_id: recipeId }, { signal });
    },

    unsaveRecipe(savedId, { signal } = {}) {
        return apiClient.delete(`/saved-recipes/${encodeURIComponent(savedId)}/`, { signal });
    },

    uploadRecipeImage(recipeId, file, { signal } = {}) {
        const form = new FormData();
        form.append("image", file);

        return apiClient.postForm(
            `/recipes/${encodeURIComponent(recipeId)}/image/`,
            form,
            { signal }
        );
    },
};

export default recipeService;

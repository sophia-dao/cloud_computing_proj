import apiClient from "./apiClient";

/**
 * Recipe submission (Issue #67).
 *
 *   POST /api/recipes/                       create (signed in; owner = you)
 *   GET  /api/recipes/duplicates/?name=...   same-name recipes, for a warning
 *   POST /api/recipes/{id}/image/            multipart "image" (owner or admin)
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

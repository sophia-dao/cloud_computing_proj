
import apiClient from "./api/apiClient";

const recipesApi = {
    getRecipes({ page = 1, signal } = {}) {
        const params = new URLSearchParams({
            page: String(page),
        });

        return apiClient.get(`/recipes/?${params.toString()}`, {
            signal,
        });
    },

    getRecipeById(id, { signal } = {}) {
        return apiClient.get(
            `/recipes/${encodeURIComponent(id)}/`,
            { signal }
        );
    },
};

export default recipesApi;

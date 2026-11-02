
import apiClient from "./api/apiClient";

const recipesApi = {

    getRecipes({
        page = 1,
        search = "",
        cuisine = "",
        diet = "",
        cost = "",
        other = "",
        allergy = "",
        signal,
    } = {}) {
        const params = new URLSearchParams({
            page: String(page),
        });

        const filters = {
            search,
            cuisine,
            diet,
            cost,
            other,
            allergy,
        };

        for (const [key, value] of Object.entries(filters)) {
            if (Array.isArray(value)) {
                value.forEach((item) => {
                    if (String(item).trim()) {
                        params.append(key, String(item).trim());
                    }
                });
            } else if (String(value ?? "").trim()) {
                params.set(key, String(value).trim());
            }
        }

        return apiClient.get(
            `/recipes/?${params.toString()}`,
            { signal }
        );
    },

    getRecipeById(id, { signal } = {}) {
        return apiClient.get(
            `/recipes/${encodeURIComponent(id)}/`,
            { signal }
        );
    },
};

export default recipesApi;

import apiClient from "./apiClient";

export const DEFAULT_INGREDIENT_PAGE_SIZE = 10;

/**
 * Normalizes paginated (`{ results: [] }`) and plain-array responses
 * from GET /api/ingredients/ into an array of `{ id, name, category }`.
 */
function toIngredientList(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    return [];
}

const ingredientService = {
    /**
     * Searches canonical ingredients on the backend.
     * Only one small page is requested so the full catalogue is never downloaded.
     */
    async searchIngredients(
        search,
        { pageSize = DEFAULT_INGREDIENT_PAGE_SIZE, signal } = {}
    ) {
        const params = new URLSearchParams({
            search: String(search ?? "").trim(),
            page_size: String(pageSize),
        });

        const data = await apiClient.get(
            `/ingredients/?${params.toString()}`,
            { signal }
        );

        return toIngredientList(data);
    },

    getIngredientById(id, { signal } = {}) {
        return apiClient.get(
            `/ingredients/${encodeURIComponent(id)}/`,
            { signal }
        );
    },
};

export default ingredientService;

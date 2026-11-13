import apiClient from "./api/apiClient";
import withAuth from "./devAuth";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

/**
 * The signed-in user's saved ingredients.
 *
 *   GET    /api/inventory/       -> { results: [{ id, ingredient: { id, name } }] }
 *   POST   /api/inventory/       { ingredient_id }  (201 new, 200 already there)
 *   DELETE /api/inventory/{id}/  (id is the inventory item's id, not the ingredient's)
 */
const inventoryService = {
    async getItems({ signal } = {}) {
        const data = await apiClient.get("/inventory/", withAuth({ signal }));

        return toList(data);
    },

    addItem(ingredientId, { signal } = {}) {
        return apiClient.post(
            "/inventory/",
            { ingredient_id: ingredientId },
            withAuth({ signal })
        );
    },

    removeItem(itemId, { signal } = {}) {
        return apiClient.delete(
            `/inventory/${encodeURIComponent(itemId)}/`,
            withAuth({ signal })
        );
    },
};

export default inventoryService;

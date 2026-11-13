import apiClient from "./api/apiClient";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

const ingredientsService = {
    /**
     * Public, paginated ingredient search.
     *   GET /api/ingredients/?search=egg&page_size=10
     */
    async search(term, { pageSize = 10, signal } = {}) {
        const params = new URLSearchParams({
            search: term,
            page_size: String(pageSize),
        });

        const data = await apiClient.get(`/ingredients/?${params}`, { signal });

        return toList(data);
    },
};

export default ingredientsService;

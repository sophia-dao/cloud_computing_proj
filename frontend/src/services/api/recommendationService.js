import apiClient from "./apiClient";

export const MATCH_MODES = {
    AVAILABLE_ONLY: "AVAILABLE_ONLY",
    PARTIAL_MATCH: "PARTIAL_MATCH",
};

const recommendationService = {
    /**
     * POST /api/recommendations/ (see docs/api-design.md §20).
     * Matching and scoring are owned by the backend RecommendationService;
     * the frontend only sends canonical IDs and renders the response.
     */
    getRecommendations(
        {
            ingredientIds = [],
            matchMode = MATCH_MODES.PARTIAL_MATCH,
            tagIds = [],
            allergenIds = [],
        } = {},
        { signal } = {}
    ) {
        return apiClient.post(
            "/recommendations/",
            {
                ingredients: ingredientIds,
                match_mode: matchMode,
                filters: {
                    allergen_ids: allergenIds,
                    tag_ids: tagIds,
                },
            },
            { signal }
        );
    },
};

export default recommendationService;

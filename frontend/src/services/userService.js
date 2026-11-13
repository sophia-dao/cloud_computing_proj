import apiClient from "./api/apiClient";
import withAuth from "./devAuth";

const userService = {
    getCurrentUser({ signal } = {}) {
        return apiClient.get("/users/me/", withAuth({ signal }));
    },

    updateCurrentUser({ displayName, profileImage }, { signal } = {}) {
        return apiClient.patch(
            "/users/me/",
            {
                display_name: displayName,
                profile_image: profileImage || null,
            },
            withAuth({ signal })
        );
    },

    async getPreferences({ signal } = {}) {
        const data = await apiClient.get(
            "/users/me/preferences/",
            withAuth({ signal })
        );

        return data?.preferences ?? [];
    },

    async updatePreferences(tagIds, { signal } = {}) {
        const data = await apiClient.put(
            "/users/me/preferences/",
            { tag_ids: tagIds },
            withAuth({ signal })
        );

        return data?.preferences ?? [];
    },

    async getAllergies({ signal } = {}) {
        const data = await apiClient.get(
            "/users/me/allergies/",
            withAuth({ signal })
        );

        return data?.allergies ?? [];
    },

    async updateAllergies(allergenIds, { signal } = {}) {
        const data = await apiClient.put(
            "/users/me/allergies/",
            { allergen_ids: allergenIds },
            withAuth({ signal })
        );

        return data?.allergies ?? [];
    },
};

export default userService;

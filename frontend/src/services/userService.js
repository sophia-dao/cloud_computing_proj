import apiClient from "./api/apiClient";

/**
 * DEV-ONLY auth shim.
 *
 * The backend currently runs on DRF's default authentication
 * (session / HTTP Basic) and the frontend has no login flow yet.
 * To exercise the protected /users/me/ endpoints locally, set
 *
 *     VITE_DEV_BASIC_AUTH=username:password
 *
 * in frontend/.env.local. It is ignored in production builds
 * (import.meta.env.DEV is false there).
 *
 * TODO: remove once real authentication (Cognito) is wired in.
 */
function withAuth(options = {}) {
    const credentials = import.meta.env.DEV
        ? import.meta.env.VITE_DEV_BASIC_AUTH
        : null;

    if (!credentials) return options;

    const headers = new Headers(options.headers);

    if (!headers.has("Authorization")) {
        headers.set("Authorization", `Basic ${btoa(credentials)}`);
    }

    return { ...options, headers };
}

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

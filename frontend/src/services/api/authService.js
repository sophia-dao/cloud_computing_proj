import apiClient from "./apiClient";

const authService = {
    /**
     * GET /api/auth/me/ — the application user for the current Cognito
     * access token (contract owned by backend issue #68).
     */
    getCurrentUser({ signal } = {}) {
        return apiClient.get("/auth/me/", { signal });
    },
};

export default authService;

/**
 * DEV-ONLY auth shim.
 *
 * The backend currently runs on DRF's default authentication
 * (session / HTTP Basic) and the frontend has no login flow yet.
 * To exercise protected endpoints locally, set
 *
 *     VITE_DEV_BASIC_AUTH=username:password
 *
 * in frontend/.env.local. It is ignored in production builds
 * (import.meta.env.DEV is false there).
 *
 * Wrap the options of any request that needs a signed-in user:
 *     apiClient.get("/inventory/", withAuth({ signal }))
 *
 * TODO: remove once real authentication (Cognito) is wired in.
 */
export default function withAuth(options = {}) {
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

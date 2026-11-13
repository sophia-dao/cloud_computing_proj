/**
 * Public Cognito configuration for the browser (no secrets).
 * The app client must be a *public* client (no client secret) with
 * Authorization Code grant + PKCE enabled.
 */

function trimSlash(value) {
    return String(value || "").trim().replace(/\/+$/, "");
}

function normalizeDomain(value) {
    const domain = trimSlash(value);
    if (!domain) return "";
    return /^https?:\/\//i.test(domain) ? domain : `https://${domain}`;
}

const origin = typeof window !== "undefined" ? window.location.origin : "";

const env = import.meta.env;

export const authConfig = Object.freeze({
    domain: normalizeDomain(env.VITE_COGNITO_DOMAIN),
    clientId: String(env.VITE_COGNITO_CLIENT_ID || "").trim(),
    redirectUri: trimSlash(env.VITE_COGNITO_REDIRECT_URI) || `${origin}/auth/callback`,
    logoutUri: String(env.VITE_COGNITO_LOGOUT_URI || "").trim() || `${origin}/`,
    scopes: String(env.VITE_COGNITO_SCOPES || "openid email profile").trim(),
    // Identity provider name as configured in the User Pool (usually "Google").
    googleProvider: String(env.VITE_COGNITO_GOOGLE_PROVIDER || "Google").trim(),
});

export const isAuthConfigured = Boolean(authConfig.domain && authConfig.clientId);

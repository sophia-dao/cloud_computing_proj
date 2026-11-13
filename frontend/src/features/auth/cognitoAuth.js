/**
 * Cognito managed login (Hosted UI) with OAuth 2.0 Authorization Code + PKCE.
 *
 * - No client secret is used or stored (public app client).
 * - Tokens are kept in sessionStorage so they survive page refreshes in the
 *   same tab but are cleared when the tab is closed. They are never put in
 *   URLs or logged.
 * - Cognito establishes identity; Django decides permissions.
 */

import { authConfig, isAuthConfigured } from "./authConfig";
import { createCodeChallenge, decodeJwtPayload, randomString } from "./pkce";

const SESSION_KEY = "recipe-app.auth.session";
const PENDING_KEY = "recipe-app.auth.pending";
const PENDING_MAX_AGE_MS = 10 * 60 * 1000;
// Refresh a little before expiry to avoid sending tokens that expire in flight.
const EXPIRY_SKEW_SECONDS = 60;

export class AuthError extends Error {
    constructor(message, code = "auth_error") {
        super(message);
        this.name = "AuthError";
        this.code = code;
    }
}

/* ------------------------------------------------------------------ */
/* Storage                                                             */
/* ------------------------------------------------------------------ */

function readJson(key) {
    try {
        const raw = window.sessionStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeJson(key, value) {
    try {
        if (value == null) window.sessionStorage.removeItem(key);
        else window.sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
        // Storage may be unavailable (private mode); auth then lasts for this page only.
    }
}

let memorySession = readJson(SESSION_KEY);
const listeners = new Set();

function setSession(session, reason = "update") {
    memorySession = session;
    writeJson(SESSION_KEY, session);
    listeners.forEach((listener) => listener(session, reason));
}

/** Subscribe to session changes. Returns an unsubscribe function. */
export function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

export function hasSession() {
    return Boolean(memorySession?.accessToken);
}

/** Non-sensitive identity claims from the ID token (for display only). */
export function getIdentityClaims() {
    const claims = decodeJwtPayload(memorySession?.idToken);
    if (!claims) return null;
    return {
        sub: claims.sub,
        email: claims.email,
        name: claims.name || claims.given_name || claims["cognito:username"],
        picture: claims.picture,
    };
}

/* ------------------------------------------------------------------ */
/* Navigation helpers                                                  */
/* ------------------------------------------------------------------ */

/** Only allow same-origin, in-app paths as post-login destinations. */
export function sanitizeReturnTo(value) {
    const path = String(value || "");
    if (!path.startsWith("/") || path.startsWith("//") || path.startsWith("/\\")) {
        return "/";
    }
    if (/^\/(login|auth\/callback)(\/|\?|#|$)/.test(path)) return "/";
    return path;
}

function requireConfig() {
    if (!isAuthConfigured) {
        throw new AuthError(
            "Sign-in is not configured. Set VITE_COGNITO_DOMAIN and VITE_COGNITO_CLIENT_ID.",
            "not_configured"
        );
    }
}

/**
 * Redirects the browser to Cognito managed login.
 * @param {object} options
 * @param {string} [options.returnTo] in-app path to return to after login
 * @param {"google"|null} [options.provider] skip the provider chooser
 * @param {boolean} [options.signUp] open the sign-up page instead of sign-in
 */
export async function beginSignIn({ returnTo = "/", provider = null, signUp = false } = {}) {
    requireConfig();

    const state = randomString(32);
    const codeVerifier = randomString(64);
    const codeChallenge = await createCodeChallenge(codeVerifier);

    writeJson(PENDING_KEY, {
        state,
        codeVerifier,
        returnTo: sanitizeReturnTo(returnTo),
        createdAt: Date.now(),
    });

    const params = new URLSearchParams({
        response_type: "code",
        client_id: authConfig.clientId,
        redirect_uri: authConfig.redirectUri,
        scope: authConfig.scopes,
        state,
        code_challenge: codeChallenge,
        code_challenge_method: "S256",
    });

    if (provider === "google") {
        params.set("identity_provider", authConfig.googleProvider);
    }

    const endpoint = signUp && !provider ? "signup" : "oauth2/authorize";
    window.location.assign(`${authConfig.domain}/${endpoint}?${params.toString()}`);
}

/* ------------------------------------------------------------------ */
/* Token endpoint                                                      */
/* ------------------------------------------------------------------ */

async function requestTokens(body) {
    let response;
    try {
        response = await fetch(`${authConfig.domain}/oauth2/token`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams(body).toString(),
            cache: "no-store",
            credentials: "omit",
        });
    } catch {
        throw new AuthError("Unable to reach the sign-in service.", "network_error");
    }

    let data;
    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok || !data?.access_token) {
        // Only surface the OAuth error code; never echo tokens.
        throw new AuthError(
            "Sign-in could not be completed. Please try again.",
            data?.error || `http_${response.status}`
        );
    }

    return data;
}

function sessionFromTokenResponse(data, previous = null) {
    const claims = decodeJwtPayload(data.access_token);
    const expiresAt = claims?.exp
        ? claims.exp
        : Math.floor(Date.now() / 1000) + Number(data.expires_in || 3600);

    return {
        accessToken: data.access_token,
        idToken: data.id_token || previous?.idToken || null,
        // Cognito does not return a new refresh token on refresh (unless rotation is on).
        refreshToken: data.refresh_token || previous?.refreshToken || null,
        expiresAt,
    };
}

const inFlightCallbacks = new Map();

/**
 * Completes the redirect from Cognito. Validates `state`, exchanges the code
 * (with the PKCE verifier) and stores the session. Safe to call twice for the
 * same URL (React StrictMode) — the exchange happens only once.
 * @returns {Promise<string>} sanitized in-app path to continue to
 */
export function handleRedirectCallback(search = window.location.search) {
    if (!inFlightCallbacks.has(search)) {
        inFlightCallbacks.set(search, completeCallback(search));
    }
    return inFlightCallbacks.get(search);
}

async function completeCallback(search) {
    requireConfig();

    const params = new URLSearchParams(search);
    const pending = readJson(PENDING_KEY);
    // The pending login is single-use regardless of outcome.
    writeJson(PENDING_KEY, null);

    const oauthError = params.get("error");
    if (oauthError) {
        const description = params.get("error_description");
        throw new AuthError(
            oauthError === "access_denied"
                ? "Sign-in was cancelled."
                : description || "Sign-in failed. Please try again.",
            oauthError
        );
    }

    const code = params.get("code");
    const state = params.get("state");

    if (!code || !state) {
        throw new AuthError("The sign-in response is incomplete.", "invalid_request");
    }

    if (!pending || pending.state !== state) {
        throw new AuthError(
            "This sign-in link is invalid or was already used. Please sign in again.",
            "state_mismatch"
        );
    }

    if (Date.now() - pending.createdAt > PENDING_MAX_AGE_MS) {
        throw new AuthError("The sign-in attempt expired. Please sign in again.", "expired_request");
    }

    const data = await requestTokens({
        grant_type: "authorization_code",
        client_id: authConfig.clientId,
        code,
        redirect_uri: authConfig.redirectUri,
        code_verifier: pending.codeVerifier,
    });

    setSession(sessionFromTokenResponse(data), "signin");
    return sanitizeReturnTo(pending.returnTo);
}

let refreshPromise = null;

async function refreshSession() {
    const current = memorySession;
    if (!current?.refreshToken) {
        throw new AuthError("Your session has expired.", "session_expired");
    }

    const data = await requestTokens({
        grant_type: "refresh_token",
        client_id: authConfig.clientId,
        refresh_token: current.refreshToken,
    });

    setSession(sessionFromTokenResponse(data, current), "refresh");
    return memorySession.accessToken;
}

/**
 * Returns a valid access token, refreshing it if needed.
 * Returns null for guests. If the session cannot be refreshed it is cleared
 * and listeners are notified with reason "expired".
 * @param {{ forceRefresh?: boolean }} [options]
 */
export async function getAccessToken({ forceRefresh = false } = {}) {
    const current = memorySession;
    if (!current?.accessToken) return null;

    const now = Math.floor(Date.now() / 1000);
    if (!forceRefresh && current.expiresAt - EXPIRY_SKEW_SECONDS > now) {
        return current.accessToken;
    }

    if (!refreshPromise) {
        refreshPromise = refreshSession()
            .catch(() => {
                expireSession();
                return null;
            })
            .finally(() => {
                refreshPromise = null;
            });
    }

    return refreshPromise;
}

/** Clears local auth state after an unrecoverable token failure. */
export function expireSession() {
    if (memorySession) setSession(null, "expired");
}

/** Clears local state and ends the Cognito managed-login session. */
export function signOut() {
    setSession(null, "signout");
    writeJson(PENDING_KEY, null);

    if (!isAuthConfigured) return;

    const params = new URLSearchParams({
        client_id: authConfig.clientId,
        logout_uri: authConfig.logoutUri,
    });
    window.location.assign(`${authConfig.domain}/logout?${params.toString()}`);
}

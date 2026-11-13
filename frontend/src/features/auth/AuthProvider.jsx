import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AuthContext } from "../../contexts/authContext";
import { useToast } from "../../hooks/useToast";
import { setAuthTokenProvider } from "../../services/api/apiClient";
import authService from "../../services/api/authService";
import { isAuthConfigured } from "./authConfig";
import {
    beginSignIn,
    expireSession,
    getAccessToken,
    getIdentityClaims,
    hasSession,
    signOut as cognitoSignOut,
    subscribe,
} from "./cognitoAuth";

// Register once at module load so the very first API call can use the token.
setAuthTokenProvider({ getToken: getAccessToken });

/**
 * Exposes authentication state to the app:
 *   status: "loading" | "authenticated" | "unauthenticated"
 *   user:   response of GET /api/auth/me/ (null until loaded / if unavailable)
 *   claims: display-only identity claims from the Cognito ID token
 */
export default function AuthProvider({ children }) {
    const { showToast } = useToast();

    const [state, setState] = useState(() => ({
        status: hasSession() ? "loading" : "unauthenticated",
        user: null,
        claims: hasSession() ? getIdentityClaims() : null,
        userError: "",
    }));

    const requestRef = useRef(null);

    const loadUser = useCallback(() => {
        requestRef.current?.abort();
        const controller = new AbortController();
        requestRef.current = controller;

        return authService
            .getCurrentUser({ signal: controller.signal })
            .then(
                (user) => ({ user }),
                (error) => ({ error })
            )
            .then(({ user, error }) => {
                if (controller.signal.aborted || error?.name === "AbortError") return;

                if (!error) {
                    setState({ status: "authenticated", user, claims: getIdentityClaims(), userError: "" });
                    return;
                }

                if (error.status === 401) {
                    // The backend rejected even a refreshed token: treat as signed out.
                    expireSession();
                    return;
                }

                // Signed in with Cognito but the profile couldn't be loaded
                // (e.g. backend unavailable). Stay signed in and surface the error.
                setState({
                    status: hasSession() ? "authenticated" : "unauthenticated",
                    user: null,
                    claims: getIdentityClaims(),
                    userError: error.message || "Unable to load your account.",
                });
            });
    }, []);

    useEffect(() => {
        const unsubscribe = subscribe((session, reason) => {
            if (session) {
                if (reason === "signin") {
                    setState((current) => ({
                        ...current,
                        status: "loading",
                        claims: getIdentityClaims(),
                    }));
                    loadUser();
                }
                return;
            }

            requestRef.current?.abort();
            setState({ status: "unauthenticated", user: null, claims: null, userError: "" });

            if (reason === "expired") {
                showToast({
                    type: "warning",
                    message: "Your session has expired. Please sign in again.",
                });
            }
        });

        if (hasSession()) loadUser();

        return () => {
            unsubscribe();
            requestRef.current?.abort();
        };
    }, [loadUser, showToast]);

    const signIn = useCallback((options) => beginSignIn(options), []);
    const signUp = useCallback(
        (options = {}) => beginSignIn({ ...options, signUp: true }),
        []
    );
    const signOut = useCallback(() => cognitoSignOut(), []);

    const value = useMemo(
        () => ({
            ...state,
            isAuthenticated: state.status === "authenticated",
            isConfigured: isAuthConfigured,
            displayName:
                state.user?.display_name ||
                state.claims?.name ||
                state.user?.email ||
                state.claims?.email ||
                "",
            signIn,
            signUp,
            signOut,
            reloadUser: loadUser,
        }),
        [state, signIn, signUp, signOut, loadUser]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

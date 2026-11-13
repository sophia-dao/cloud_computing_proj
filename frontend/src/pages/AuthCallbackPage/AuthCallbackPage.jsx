import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Spinner from "../../components/common/Spinner/Spinner";
import { handleRedirectCallback } from "../../features/auth/cognitoAuth";

import "../../features/auth/auth.css";

/**
 * Landing route for the Cognito redirect (/auth/callback?code=…&state=…).
 * Exchanges the code, then replaces the URL so the code never stays in
 * browser history.
 */
export default function AuthCallbackPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;

        handleRedirectCallback(location.search)
            .then((returnTo) => {
                if (active) navigate(returnTo, { replace: true });
            })
            .catch((err) => {
                if (!active) return;
                // Drop the code/state from the address bar on failure too.
                window.history.replaceState(null, "", location.pathname);
                setError(err?.message || "Sign-in failed. Please try again.");
            });

        return () => {
            active = false;
        };
    }, [location.search, location.pathname, navigate]);

    return (
        <section className="auth-page auth-page--centered">
            {error ? (
                <div className="auth-card" role="alert">
                    <h1 className="auth-card__title">We couldn&apos;t sign you in</h1>
                    <p className="auth-card__text">{error}</p>
                    <div className="auth-card__actions">
                        <Link to="/login" className="ui-button ui-button--primary ui-button--md">
                            Try again
                        </Link>
                        <Link to="/recipes" className="auth-card__link">
                            Continue as guest →
                        </Link>
                    </div>
                </div>
            ) : (
                <>
                    <Spinner label="Completing sign-in…" />
                    <p className="auth-card__text">Completing sign-in…</p>
                </>
            )}
        </section>
    );
}

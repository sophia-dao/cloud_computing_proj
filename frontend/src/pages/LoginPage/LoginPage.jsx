import { useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";

import Button from "../../components/common/Button/Button";
import Spinner from "../../components/common/Spinner/Spinner";
import { sanitizeReturnTo } from "../../features/auth/cognitoAuth";
import { useAuth } from "../../hooks/useAuth";

import "../../features/auth/auth.css";

function GoogleIcon() {
    return (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.56-5.17 3.56-8.81z" />
            <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.92l-3.88-3c-1.07.72-2.45 1.15-4.06 1.15-3.12 0-5.77-2.11-6.71-4.95H1.28v3.1A12 12 0 0 0 12 24z" />
            <path fill="#FBBC05" d="M5.29 14.28A7.2 7.2 0 0 1 4.91 12c0-.79.14-1.56.38-2.28v-3.1H1.28a12 12 0 0 0 0 10.76l4.01-3.1z" />
            <path fill="#EA4335" d="M12 4.77c1.76 0 3.34.61 4.59 1.8l3.44-3.44A11.5 11.5 0 0 0 12 0 12 12 0 0 0 1.28 6.62l4.01 3.1C6.23 6.88 8.88 4.77 12 4.77z" />
        </svg>
    );
}

export default function LoginPage() {
    const { status, isConfigured, signIn, signUp } = useAuth();
    const [searchParams] = useSearchParams();
    const [redirecting, setRedirecting] = useState(false);
    const [error, setError] = useState("");

    const returnTo = sanitizeReturnTo(searchParams.get("returnTo") || "/");

    if (status === "authenticated") {
        return <Navigate to={returnTo} replace />;
    }

    async function start(action) {
        setError("");
        setRedirecting(true);
        try {
            await action({ returnTo });
        } catch (err) {
            setRedirecting(false);
            setError(err?.message || "Unable to start sign-in.");
        }
    }

    return (
        <section className="auth-page">
            <div className="auth-card">
                <span className="auth-card__eyebrow">Welcome</span>
                <h1 className="auth-card__title">Sign in to save your kitchen</h1>
                <p className="auth-card__text">
                    Keep your inventory, preferences and allergies across visits.
                    You can still browse recipes without an account.
                </p>

                {!isConfigured ? (
                    <p className="auth-card__error" role="alert">
                        Sign-in isn&apos;t configured for this environment yet.
                    </p>
                ) : status === "loading" ? (
                    <Spinner label="Checking your session…" />
                ) : (
                    <div className="auth-card__actions">
                        <button
                            type="button"
                            className="auth-google-button"
                            onClick={() => start((opts) => signIn({ ...opts, provider: "google" }))}
                            disabled={redirecting}
                        >
                            <GoogleIcon />
                            Continue with Google
                        </button>

                        <div className="auth-card__divider"><span>or</span></div>

                        <Button
                            variant="secondary"
                            onClick={() => start(signIn)}
                            disabled={redirecting}
                        >
                            Sign in with email
                        </Button>

                        <Button
                            variant="ghost"
                            onClick={() => start(signUp)}
                            disabled={redirecting}
                        >
                            Create an account
                        </Button>
                    </div>
                )}

                {redirecting && (
                    <p className="auth-card__text auth-card__text--small" role="status">
                        Redirecting to secure sign-in…
                    </p>
                )}

                {error && (
                    <p className="auth-card__error" role="alert">{error}</p>
                )}

                <Link to="/recipes" className="auth-card__link">
                    Continue as guest →
                </Link>
            </div>
        </section>
    );
}

import { Navigate, useLocation } from "react-router-dom";

import Spinner from "../../components/common/Spinner/Spinner";
import { useAuth } from "../../hooks/useAuth";

/**
 * Client-side route guard for pages that need a signed-in user.
 * This is a UX convenience only — Django enforces authorization.
 */
export default function ProtectedRoute({ children }) {
    const { status } = useAuth();
    const location = useLocation();

    if (status === "loading") {
        return (
            <div className="auth-page auth-page--centered">
                <Spinner label="Checking your session…" />
            </div>
        );
    }

    if (status !== "authenticated") {
        const returnTo = `${location.pathname}${location.search}${location.hash}`;
        return (
            <Navigate
                to={`/login?returnTo=${encodeURIComponent(returnTo)}`}
                replace
            />
        );
    }

    return children;
}

import { useAuth } from "../../hooks/useAuth";

import "./auth.css";

/** Signed-in user's name and a sign-out button for the site header. */
export default function AccountControls() {
    const { isAuthenticated, displayName, signOut } = useAuth();

    if (!isAuthenticated) return null;

    return (
        <span className="auth-account">
            {displayName && (
                <span className="auth-account__name" title={displayName}>
                    {displayName}
                </span>
            )}
            <button type="button" className="auth-account__signout" onClick={signOut}>
                Sign out
            </button>
        </span>
    );
}

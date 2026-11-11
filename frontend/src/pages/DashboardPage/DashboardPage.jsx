import { Link } from "react-router-dom";

import EmptyState from "../../components/common/EmptyState/EmptyState";
import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import UserSummary from "../../features/dashboard/components/UserSummary";
import { InventoryPanel } from "../../features/inventory";
import useCurrentUser from "../../hooks/useCurrentUser";

import "./DashboardPage.css";

const LINK_BUTTON = "dashboard-page__link ui-button ui-button--md";

export default function DashboardPage() {
    const { status, user, error, reload } = useCurrentUser();

    let content;

    if (status === "loading") {
        content = (
            <div className="dashboard-page__center">
                <Spinner label="Loading your dashboard..." />
            </div>
        );
    } else if (status === "guest") {
        content = (
            <EmptyState
                icon="🔒"
                title="Sign in to see your dashboard"
                description="Your saved ingredients and profile live here once you're signed in. You can still browse recipes without an account."
                action={
                    <div className="dashboard-page__actions">
                        <Link to="/login" className={`${LINK_BUTTON} ui-button--primary`}>
                            Sign in
                        </Link>
                        <Link to="/recipes" className={`${LINK_BUTTON} ui-button--secondary`}>
                            Browse recipes
                        </Link>
                    </div>
                }
            />
        );
    } else if (status === "error") {
        content = (
            <ErrorState
                title="Unable to load your dashboard"
                description={error.message}
                onRetry={reload}
            />
        );
    } else {
        content = (
            <>
                <UserSummary user={user} />
                <InventoryPanel />
                <p className="dashboard-page__footer">
                    <Link to="/recipes">Browse recipes &rarr;</Link>
                </p>
            </>
        );
    }

    return (
        <section className="dashboard-page">
            <h1>Dashboard</h1>
            {content}
        </section>
    );
}

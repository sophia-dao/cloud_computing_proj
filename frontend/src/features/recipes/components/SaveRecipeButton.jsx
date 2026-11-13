import { Link, useLocation } from "react-router-dom";

import Button from "../../../components/common/Button/Button";
import useSavedRecipe from "../hooks/useSavedRecipe";

import "./SaveRecipeButton.css";

/** Save / unsave a recipe (Issue #14). Guests get a sign-in link instead. */
export default function SaveRecipeButton({ recipeId }) {
    const { isAuthenticated, loading, saved, busy, toggle } = useSavedRecipe(recipeId);
    const location = useLocation();

    if (!isAuthenticated) {
        const returnTo = `${location.pathname}${location.search}`;

        return (
            <Link
                to={`/login?returnTo=${encodeURIComponent(returnTo)}`}
                className="save-recipe save-recipe--link"
            >
                Sign in to save this recipe
            </Link>
        );
    }

    return (
        <Button
            variant={saved ? "secondary" : "primary"}
            size="sm"
            className="save-recipe"
            aria-pressed={saved}
            disabled={loading || busy}
            onClick={toggle}
        >
            {saved ? "★ Saved" : "☆ Save recipe"}
        </Button>
    );
}

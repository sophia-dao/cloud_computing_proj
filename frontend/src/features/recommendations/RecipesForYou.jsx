import { Link } from "react-router-dom";

import EmptyState from "../../components/common/EmptyState/EmptyState";
import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import RecipeCard from "../../components/recipes/RecipeCard/RecipeCard";
import useRecipesForYou from "./hooks/useRecipesForYou";

import "./RecipesForYou.css";

const LINK_BUTTON = "recipes-for-you__link ui-button ui-button--md";

const MAX_MISSING_SHOWN = 3;

function Intro({ authenticated, source }) {
    if (source === "ingredients") {
        return (
            <>
                <h2 id="recipes-for-you-title">Recipes for You</h2>
                <p>
                    Recipes that use the ingredients you&apos;ve saved, best
                    matches first.
                </p>
            </>
        );
    }

    if (source === "preferences") {
        return (
            <>
                <h2 id="recipes-for-you-title">Recipes for You</h2>
                <p>
                    Picked using your saved preferences. Save the ingredients
                    you have on your dashboard to see what you can make.
                </p>
            </>
        );
    }

    if (authenticated) {
        return (
            <>
                <h2 id="recipes-for-you-title">Popular recipes</h2>
                <p>
                    Save the ingredients you have on your dashboard, or{" "}
                    <Link to="/profile">add your preferences</Link>, to get
                    recipes picked for you.
                </p>
            </>
        );
    }

    return (
        <>
            <h2 id="recipes-for-you-title">Explore recipes</h2>
            <p>
                <Link to="/login">Sign in</Link> and save your preferences to
                get recipes picked for you.
            </p>
        </>
    );
}

function MatchSummary({ match }) {
    const { have, total, missing } = match;

    if (missing.length === 0) {
        return (
            <p className="recipes-for-you__match">You have every ingredient</p>
        );
    }

    const shown = missing.slice(0, MAX_MISSING_SHOWN);
    const more = missing.length - shown.length;

    return (
        <p className="recipes-for-you__match">
            You have {have} of {total} ingredients
            <span className="recipes-for-you__missing">
                Missing: {shown.join(", ")}
                {more > 0 && ` +${more} more`}
            </span>
        </p>
    );
}

export default function RecipesForYou() {
    const { loading, authenticated, source, recipes, error, reload } =
        useRecipesForYou();

    let body;

    if (loading) {
        body = (
            <div className="recipes-for-you__center">
                <Spinner label="Loading recipes..." />
            </div>
        );
    } else if (error) {
        body = (
            <ErrorState
                title="Unable to load recipes"
                description={error}
                onRetry={reload}
            />
        );
    } else if (recipes.length === 0) {
        body = authenticated ? (
            <EmptyState
                icon="🍽️"
                title="No matching recipes yet"
                description="Nothing matches your saved preferences and allergies yet. Try adjusting them in your profile."
                action={
                    <Link
                        to="/profile"
                        className={`${LINK_BUTTON} ui-button--secondary`}
                    >
                        Edit profile
                    </Link>
                }
            />
        ) : (
            <EmptyState
                icon="🍽️"
                title="No recipes available yet"
                description="Check back soon."
            />
        );
    } else {
        body = (
            <>
                <div className="recipes-for-you__grid">
                    {recipes.map((recipe) =>
                        recipe.match ? (
                            <div key={recipe.id} className="recipes-for-you__item">
                                <RecipeCard recipe={recipe} />
                                <MatchSummary match={recipe.match} />
                            </div>
                        ) : (
                            <RecipeCard key={recipe.id} recipe={recipe} />
                        )
                    )}
                </div>

                <div className="recipes-for-you__more">
                    <Link
                        to="/recipes"
                        className={`${LINK_BUTTON} ui-button--primary`}
                    >
                        Browse all recipes
                    </Link>
                </div>
            </>
        );
    }

    return (
        <section className="recipes-for-you" aria-labelledby="recipes-for-you-title">
            <header className="recipes-for-you__header">
                {loading ? (
                    <h2 id="recipes-for-you-title">Recipes</h2>
                ) : (
                    <Intro authenticated={authenticated} source={source} />
                )}
            </header>

            {body}

            {authenticated && !loading && !error && (
                <p className="recipes-for-you__notice">
                    * Allergen information is still being verified. Recipes
                    are not guaranteed to be allergen-free.
                </p>
            )}
        </section>
    );
}
